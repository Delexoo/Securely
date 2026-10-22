namespace Securely.Core;

/// <summary>Scan modes preserved from the Securely product.</summary>
public enum MonitorMode
{
    Idle,
    QuickScan,
    Timed,
    Continuous,
}

public enum ThreatClass
{
    Safe,
    Suspicious,
    Malicious,
    Unsure,
    LegitimateLogin,
    LegitimatePayment,
}

/// <summary>Placeholder until ScreenMonitor is ported from SecurelyCore.</summary>
public sealed class MonitorController
{
    public MonitorMode Mode { get; private set; } = MonitorMode.Idle;
    public bool HitboxesEnabled { get; set; }
    public bool TestMode { get; set; }
    public bool NotificationsEnabled { get; set; } = true;
    public bool SoundEnabled { get; set; } = true;
    public int TimedMinutes { get; set; } = 15;

    public void RequestQuickScan() => Mode = MonitorMode.QuickScan;
    public void RequestTimed(int minutes)
    {
        TimedMinutes = Math.Clamp(minutes, 1, 60);
        Mode = MonitorMode.Timed;
    }
    public void RequestContinuous() => Mode = MonitorMode.Continuous;
    public void Stop() => Mode = MonitorMode.Idle;
}
