using System.Speech.AudioFormat;
using NAudio.CoreAudioApi;
using NAudio.Wave;

namespace SecurelyShell;

internal readonly record struct AudioEndpoint(string Id, string Name);

internal sealed class AudioIO : IDisposable
{
    private readonly object gate = new();
    private string inputId = "";
    private string outputId = "";
    private WasapiOut? player;
    private AudioFileReader? reader;
    private MMDevice? outputDevice;
    private bool disposed;

    public bool SetDevices(string input, string output)
    {
        lock (gate)
        {
            var inputChanged = !string.Equals(inputId, input, StringComparison.Ordinal);
            inputId = input;
            outputId = output;
            return inputChanged;
        }
    }

    public (AudioEndpoint[] Inputs, AudioEndpoint[] Outputs) List()
    {
        using var enumerator = new MMDeviceEnumerator();
        return (Endpoints(enumerator, DataFlow.Capture), Endpoints(enumerator, DataFlow.Render));
    }

    public SpeechAudioSource OpenCapture()
    {
        var enumerator = new MMDeviceEnumerator();
        MMDevice device;
        lock (gate)
        {
            device = Resolve(enumerator, DataFlow.Capture, Role.Communications, inputId);
        }
        return new SpeechAudioSource(enumerator, device);
    }

    public void Play(string path)
    {
        if (!File.Exists(path)) throw new FileNotFoundException("That sound is not on this computer.", path);
        lock (gate)
        {
            if (disposed) return;
            StopPlayer();
            using var enumerator = new MMDeviceEnumerator();
            var device = Resolve(enumerator, DataFlow.Render, Role.Multimedia, outputId);
            try
            {
                reader = new AudioFileReader(path);
                player = new WasapiOut(device, AudioClientShareMode.Shared, true, 80);
                player.Init(reader);
                player.Play();
                outputDevice = device;
            }
            catch
            {
                StopPlayer();
                device.Dispose();
                throw;
            }
        }
    }

    public void Dispose()
    {
        lock (gate)
        {
            if (disposed) return;
            disposed = true;
            StopPlayer();
        }
    }

    private void StopPlayer()
    {
        try { player?.Stop(); } catch { /* already stopped */ }
        try { player?.Dispose(); } catch { /* already disposed */ }
        try { reader?.Dispose(); } catch { /* already disposed */ }
        try { outputDevice?.Dispose(); } catch { /* already disposed */ }
        player = null;
        reader = null;
        outputDevice = null;
    }

    private static AudioEndpoint[] Endpoints(MMDeviceEnumerator enumerator, DataFlow flow)
    {
        var list = new List<AudioEndpoint>();
        foreach (var device in enumerator.EnumerateAudioEndPoints(flow, DeviceState.Active))
        {
            using (device)
            {
                var name = device.FriendlyName?.Trim();
                if (string.IsNullOrWhiteSpace(device.ID) || string.IsNullOrWhiteSpace(name)) continue;
                list.Add(new AudioEndpoint(device.ID, name));
            }
        }
        return list.ToArray();
    }

    private static MMDevice Resolve(MMDeviceEnumerator enumerator, DataFlow flow, Role role, string id)
    {
        if (!string.IsNullOrWhiteSpace(id))
        {
            try
            {
                var chosen = enumerator.GetDevice(id);
                if (chosen.State == DeviceState.Active && chosen.DataFlow == flow) return chosen;
                chosen.Dispose();
            }
            catch
            {
                /* The saved device was unplugged. Use the Windows default. */
            }
        }
        return enumerator.GetDefaultAudioEndpoint(flow, role);
    }
}

internal sealed class SpeechAudioSource : Stream
{
    private readonly MMDeviceEnumerator enumerator;
    private readonly MMDevice device;
    private readonly WasapiCapture capture;
    private readonly LockedWaveBuffer buffer;
    private readonly MediaFoundationResampler? resampler;
    private readonly IWaveProvider provider;
    private int closed;

    public SpeechAudioSource(MMDeviceEnumerator enumerator, MMDevice device)
    {
        this.enumerator = enumerator;
        this.device = device;
        capture = new WasapiCapture(device, true, 50) { ShareMode = AudioClientShareMode.Shared };
        LockedWaveBuffer? ready = null;
        capture.DataAvailable += (_, args) => ready?.Add(args.Buffer, args.BytesRecorded);
        capture.StartRecording();
        ready = buffer = new LockedWaveBuffer(capture.WaveFormat);
        var target = new WaveFormat(16000, 16, 1);
        if (capture.WaveFormat.Encoding == WaveFormatEncoding.Pcm
            && capture.WaveFormat.SampleRate == 16000
            && capture.WaveFormat.BitsPerSample == 16
            && capture.WaveFormat.Channels == 1)
        {
            provider = buffer;
        }
        else
        {
            resampler = new MediaFoundationResampler(buffer, target) { ResamplerQuality = 60 };
            provider = resampler;
        }
        Format = new SpeechAudioFormatInfo(16000, AudioBitsPerSample.Sixteen, AudioChannel.Mono);
    }

    public SpeechAudioFormatInfo Format { get; }

    public override bool CanRead => true;
    public override bool CanSeek => false;
    public override bool CanWrite => false;
    public override long Length => throw new NotSupportedException();
    public override long Position
    {
        get => throw new NotSupportedException();
        set => throw new NotSupportedException();
    }

    public override void Flush() { }

    public override int Read(byte[] destination, int offset, int count)
    {
        var waited = 0;
        while (Volatile.Read(ref closed) == 0)
        {
            var read = provider.Read(destination, offset, count);
            if (read > 0) return read;
            if (waited >= 2000) return 0;
            Thread.Sleep(15);
            waited += 15;
        }
        return 0;
    }

    public override long Seek(long offset, SeekOrigin origin) => throw new NotSupportedException();
    public override void SetLength(long value) => throw new NotSupportedException();
    public override void Write(byte[] destination, int offset, int count) => throw new NotSupportedException();

    protected override void Dispose(bool disposing)
    {
        if (disposing && Interlocked.Exchange(ref closed, 1) == 0)
        {
            try { capture.StopRecording(); } catch { /* already stopped */ }
            try { resampler?.Dispose(); } catch { /* already disposed */ }
            try { capture.Dispose(); } catch { /* already disposed */ }
            try { device.Dispose(); } catch { /* already disposed */ }
            try { enumerator.Dispose(); } catch { /* already disposed */ }
        }
        base.Dispose(disposing);
    }

    private sealed class LockedWaveBuffer : IWaveProvider
    {
        private readonly BufferedWaveProvider inner;

        public LockedWaveBuffer(WaveFormat format)
        {
            inner = new BufferedWaveProvider(format)
            {
                DiscardOnBufferOverflow = true,
                BufferDuration = TimeSpan.FromSeconds(5),
            };
            WaveFormat = format;
        }

        public WaveFormat WaveFormat { get; }

        public void Add(byte[] samples, int count)
        {
            lock (inner) inner.AddSamples(samples, 0, count);
        }

        public int Read(byte[] destination, int offset, int count)
        {
            lock (inner) return inner.Read(destination, offset, count);
        }
    }
}
