using System;
using System.IO;
using System.Text;

namespace SecurelyCore;

public sealed class AuditLogger
{
    private readonly string _logFilePath;
    private readonly object _lock = new();

    public AuditLogger(string? logFilePath = null)
    {
        var baseDir = AppContext.BaseDirectory;
        _logFilePath = string.IsNullOrWhiteSpace(logFilePath)
            ? Path.Combine(baseDir, "securely_log.txt")
            : logFilePath;
    }

    public string LogFilePath => _logFilePath;

    public void LogEvent(string msg, string? threatType = null, string? description = null, string? textContent = null)
    {
        // Mirrors Securely.py log_event formatting:
        // [MM/DD/YYYY] [H:MM AM/PM] Problem
        var datePart = DateTime.Now.ToString("MM/dd/yyyy");
        var timePart = DateTime.Now.ToString("hh:mm tt").TrimStart('0');

        var logMsg = $"[{datePart}] [{timePart}] {msg}";
        lock (_lock)
        {
            File.AppendAllText(_logFilePath, logMsg + Environment.NewLine, Encoding.UTF8);
        }
    }

    public void LogInfo(string message) => WriteConsole(message, ConsoleColor.Gray);
    public void LogWarning(string message) => WriteConsole(message, ConsoleColor.Yellow);
    public void LogError(string message) => WriteConsole(message, ConsoleColor.Red);

    private static void WriteConsole(string message, ConsoleColor color)
    {
        try
        {
            var prev = Console.ForegroundColor;
            Console.ForegroundColor = color;
            Console.WriteLine(message);
            Console.ForegroundColor = prev;
        }
        catch
        {
            // ignore console formatting errors
        }
    }
}

