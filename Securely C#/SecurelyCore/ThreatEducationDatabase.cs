using System;
using System.Collections.Generic;
using System.Linq;

namespace SecurelyCore;

public sealed class ThreatEducationInfo
{
    public required string Name { get; init; }
    public required string Description { get; init; }
    public required IReadOnlyList<string> Risks { get; init; }
    public required IReadOnlyList<string> Prevention { get; init; }
}

public static class ThreatEducationDatabase
{
    // Ported from Securely.py THREAT_EDUCATION (subset visible in that file).
    // If you add more keys to Securely.py later, extend this database similarly.
    private static readonly Dictionary<string, ThreatEducationInfo> ThreatEducation = new(StringComparer.OrdinalIgnoreCase)
    {
        ["virus"] = new ThreatEducationInfo
        {
            Name = "Computer Virus",
            Description = "A computer virus is malicious software that infects files and spreads to other programs or computers. It can corrupt data, steal information, or damage your system.",
            Risks = new[] { "Data corruption", "System crashes", "Identity theft", "Performance degradation" },
            Prevention = new[] { "Keep antivirus updated", "Don't open suspicious attachments", "Avoid pirated software", "Regular system scans" }
        },
        ["malware"] = new ThreatEducationInfo
        {
            Name = "Malicious Software (Malware)",
            Description = "Malware is any software designed to harm your computer, steal data, or gain unauthorized access. It includes viruses, trojans, spyware, and ransomware.",
            Risks = new[] { "Data theft", "Financial loss", "System compromise", "Privacy invasion" },
            Prevention = new[] { "Use reputable antivirus", "Keep software updated", "Avoid suspicious downloads", "Enable firewall" }
        },
        ["phishing"] = new ThreatEducationInfo
        {
            Name = "Phishing Attack",
            Description = "Phishing is a cybercrime where attackers impersonate legitimate organizations to steal sensitive information like passwords, credit card numbers, or personal data.",
            Risks = new[] { "Identity theft", "Financial fraud", "Account takeover", "Data breach" },
            Prevention = new[] { "Verify sender authenticity", "Check URLs carefully", "Never share passwords via email", "Use two-factor authentication" }
        },
        ["ransomware"] = new ThreatEducationInfo
        {
            Name = "Ransomware",
            Description = "Ransomware encrypts your files and demands payment for the decryption key. It can lock you out of your own data and systems.",
            Risks = new[] { "Data loss", "Financial extortion", "Business disruption", "Permanent file damage" },
            Prevention = new[] { "Regular backups", "Keep systems updated", "Employee training", "Network segmentation" }
        },
        ["trojan"] = new ThreatEducationInfo
        {
            Name = "Trojan Horse",
            Description = "A trojan appears as legitimate software but contains malicious code. It can create backdoors, steal data, or download additional malware.",
            Risks = new[] { "Remote access", "Data theft", "System compromise", "Additional malware installation" },
            Prevention = new[] { "Download from trusted sources", "Read software reviews", "Use antivirus protection", "Check digital signatures" }
        },
        ["spyware"] = new ThreatEducationInfo
        {
            Name = "Spyware",
            Description = "Spyware secretly monitors your activities, collects personal information, and sends it to third parties without your knowledge or consent.",
            Risks = new[] { "Privacy invasion", "Identity theft", "Financial fraud", "Personal data exposure" },
            Prevention = new[] { "Use anti-spyware tools", "Avoid free suspicious software", "Read privacy policies", "Regular system scans" }
        },
        ["adware"] = new ThreatEducationInfo
        {
            Name = "Advertising Software (Adware)",
            Description = "Adware displays unwanted advertisements and may track your browsing habits. While not always malicious, it can slow your system and compromise privacy.",
            Risks = new[] { "Privacy concerns", "System slowdown", "Unwanted ads", "Browser hijacking" },
            Prevention = new[] { "Use ad blockers", "Avoid bundled software", "Read installation prompts carefully", "Use reputable software sources" }
        },
        ["keylogger"] = new ThreatEducationInfo
        {
            Name = "Keylogger",
            Description = "A keylogger records every keystroke you make, potentially capturing passwords, credit card numbers, and other sensitive information.",
            Risks = new[] { "Password theft", "Financial fraud", "Identity theft", "Account compromise" },
            Prevention = new[] { "Use virtual keyboards for sensitive input", "Enable keystroke encryption", "Regular malware scans", "Monitor account activity" }
        },
        ["rootkit"] = new ThreatEducationInfo
        {
            Name = "Rootkit",
            Description = "A rootkit hides deep in your system to maintain persistent access while concealing its presence from security software and users.",
            Risks = new[] { "Complete system compromise", "Persistent backdoor access", "Data theft", "Difficult detection" },
            Prevention = new[] { "Use rootkit scanners", "Keep OS updated", "Avoid suspicious downloads", "Regular security audits" }
        },
        ["botnet"] = new ThreatEducationInfo
        {
            Name = "Botnet",
            Description = "A botnet is a network of infected computers controlled remotely by cybercriminals to perform coordinated attacks or illegal activities.",
            Risks = new[] { "Becoming part of cybercrime", "Legal liability", "System performance issues", "Data theft" },
            Prevention = new[] { "Keep systems patched", "Use reputable antivirus", "Monitor network traffic", "Regular security updates" }
        }
    };

    public static ThreatEducationInfo GetThreatEducation(string threatKeyword)
    {
        var threatLower = threatKeyword.ToLowerInvariant();

        foreach (var (key, info) in ThreatEducation)
        {
            if (threatLower.Contains(key, StringComparison.OrdinalIgnoreCase) ||
                key.Contains(threatLower, StringComparison.OrdinalIgnoreCase))
            {
                return info;
            }
        }

        return new ThreatEducationInfo
        {
            Name = "Security Threat",
            Description = "This appears to be a security-related term that requires attention. It may indicate potential malicious activity or suspicious content.",
            Risks = new[] { "Potential system compromise", "Data security concerns", "Privacy risks", "Unknown threats" },
            Prevention = new[] { "Exercise caution", "Verify legitimacy", "Keep security software updated", "Report suspicious activity" }
        };
    }
}

