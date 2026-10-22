using System;
using System.Collections.Generic;
using System.Drawing;
using System.Drawing.Imaging;
using System.IO;
using System.Threading;
using System.Threading.Tasks;
using System.Windows.Forms;
using TesseractOCR;
using TesseractOCR.Enums;

namespace SecurelyCore;

public sealed class CaptureResult : IDisposable
{
    public required Bitmap Bitmap { get; init; }
    public required byte[] PngBytes { get; init; }

    public string Base64 => Convert.ToBase64String(PngBytes);

    public void Dispose()
    {
        try { Bitmap.Dispose(); } catch { }
    }
}

public sealed class OcrWordBox
{
    public required string Text { get; init; }
    public required int Confidence { get; init; }
    public required int Left { get; init; }
    public required int Top { get; init; }
    public required int Width { get; init; }
    public required int Height { get; init; }
}

public sealed class OcrResult
{
    public required string FullText { get; init; }
    public required IReadOnlyList<OcrWordBox> Words { get; init; }
}

public interface IScreenCaptureService
{
    Task<CaptureResult> CapturePrimaryMonitorAsync(CancellationToken cancellationToken);
}

public interface IOcrService
{
    Task<OcrResult> AnalyzeAsync(Bitmap image, CancellationToken cancellationToken);
}

public sealed class GdiScreenCaptureService : IScreenCaptureService
{
    public Task<CaptureResult> CapturePrimaryMonitorAsync(CancellationToken cancellationToken)
    {
        // Port intent: capture primary monitor only.
        // Securely.py uses mss + custom primary monitor safety logic.
        // Here we use WinForms Screen.PrimaryScreen as a pragmatic equivalent.
        var bounds = Screen.PrimaryScreen.Bounds;
        var width = bounds.Width;
        var height = bounds.Height;

        var bmp = new Bitmap(width, height, PixelFormat.Format32bppArgb);
        using var g = Graphics.FromImage(bmp);

        // CopyFromScreen uses coordinates relative to virtual screen space.
        g.CopyFromScreen(bounds.Left, bounds.Top, 0, 0, new Size(width, height), CopyPixelOperation.SourceCopy);

        var pngBytes = BitmapToPngBytes(bmp);
        return Task.FromResult(new CaptureResult { Bitmap = bmp, PngBytes = pngBytes });
    }

    private static byte[] BitmapToPngBytes(Bitmap bmp)
    {
        using var ms = new MemoryStream();
        bmp.Save(ms, System.Drawing.Imaging.ImageFormat.Png);
        return ms.ToArray();
    }
}

/// <summary>
/// OCR service backed by TesseractOCR (wrapper from NuGet).
/// If tessdata is missing, it falls back to "OCR off" mode (empty results).
/// </summary>
public sealed class TesseractOcrService : IOcrService
{
    private readonly string _language;
    private readonly string _tessDataPath;
    private readonly EngineMode _engineMode;

    public TesseractOcrService(string language = "eng", string? tessDataPath = null, EngineMode? engineMode = null)
    {
        _language = language;
        _tessDataPath = tessDataPath ?? DetectTessDataPath();
        _engineMode = engineMode ?? EngineMode.Default;
    }

    public Task<OcrResult> AnalyzeAsync(Bitmap image, CancellationToken cancellationToken)
    {
        if (string.IsNullOrWhiteSpace(_tessDataPath) || !Directory.Exists(_tessDataPath))
        {
            return Task.FromResult(new OcrResult
            {
                FullText = string.Empty,
                Words = System.Array.Empty<OcrWordBox>()
            });
        }

        cancellationToken.ThrowIfCancellationRequested();

        // TesseractOCR doesn't accept System.Drawing.Bitmap directly; convert to image bytes.
        // Using PNG gives the most predictable results.
        byte[] imageBytes;
        using (var ms = new MemoryStream())
        {
            image.Save(ms, System.Drawing.Imaging.ImageFormat.Png);
            imageBytes = ms.ToArray();
        }

        using var engine = new Engine(_tessDataPath, _language == "eng" ? Language.English : Language.English, _engineMode);
        using var pix = TesseractOCR.Pix.Image.LoadFromMemory(imageBytes);
        using var page = engine.Process(pix);

        var fullText = page.Text ?? string.Empty;

        var words = new List<OcrWordBox>();
        foreach (var block in page.Layout)
        {
            foreach (var paragraph in block.Paragraphs)
            {
                foreach (var line in paragraph.TextLines)
                {
                    foreach (var word in line.Words)
                    {
                        cancellationToken.ThrowIfCancellationRequested();

                        var wordText = word.Text;
                        if (string.IsNullOrWhiteSpace(wordText))
                            continue;

                        var conf = (int)word.Confidence;
                        if (word.BoundingBox is null)
                            continue;

                        var boundingBox = word.BoundingBox.Value;

                        var left = (int)boundingBox.X1;
                        var top = (int)boundingBox.Y1;
                        var width = (int)boundingBox.Width;
                        var height = (int)boundingBox.Height;

                        if (width <= 0 || height <= 0)
                            continue;

                        words.Add(new OcrWordBox
                        {
                            Text = wordText,
                            Confidence = conf,
                            Left = left,
                            Top = top,
                            Width = width,
                            Height = height
                        });
                    }
                }
            }
        }

        return Task.FromResult(new OcrResult
        {
            FullText = fullText,
            Words = words
        });
    }

    private static string DetectTessDataPath()
    {
        var env = Environment.GetEnvironmentVariable("TESSDATA_PREFIX");
        if (!string.IsNullOrWhiteSpace(env))
            return env;

        var appBase = AppContext.BaseDirectory;
        var direct = Path.Combine(appBase, "tessdata");
        return Directory.Exists(direct) ? direct : string.Empty;
    }
}

