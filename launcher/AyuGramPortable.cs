// AyuGramPortable.exe — .NET Framework launcher with the ORIGINAL app icon.
// Native AyuGram executable is always kept in App\AyuGram.
// All normal Telegram/AyuGram working data goes into the portable Data folder.
using System;
using System.Diagnostics;
using System.IO;
using System.Text;
using System.Windows.Forms;

internal static class AyuGramPortableLauncher
{
    [STAThread]
    private static void Main(string[] args)
    {
        try
        {
            string root = Path.GetFullPath(AppDomain.CurrentDomain.BaseDirectory);
            string application = Path.Combine(root, @"App\AyuGram\AyuGram.exe");
            string workDir = Path.Combine(root, "Data");

            if (!File.Exists(application))
            {
                MessageBox.Show("Cannot find App\\AyuGram\\AyuGram.exe.\n\nRe-extract the complete portable ZIP.",
                    "AyuGram Portable", MessageBoxButtons.OK, MessageBoxIcon.Error);
                return;
            }

            Directory.CreateDirectory(workDir);
            Directory.CreateDirectory(Path.Combine(workDir, "Downloads"));

            // A supported Telegram Desktop CLI flag inherited by AyuGram.
            // The workdir contains the tdata subfolder, logs and updater cache.
            StringBuilder arguments = new StringBuilder();
            arguments.Append("-workdir ").Append(Quote(workDir));
            arguments.Append(" -noupdate");

            // Pass along optional arguments, e.g. tg:// links. Do not allow a
            // caller to override -workdir and escape the portable Data folder.
            for (int i = 0; i < args.Length; ++i)
            {
                if (string.Equals(args[i], "-workdir", StringComparison.OrdinalIgnoreCase) ||
                    string.Equals(args[i], "-workpath", StringComparison.OrdinalIgnoreCase))
                {
                    MessageBox.Show("-workdir and -workpath overrides are not permitted by this portable launcher.",
                        "AyuGram Portable", MessageBoxButtons.OK, MessageBoxIcon.Warning);
                    return;
                }
                arguments.Append(' ').Append(Quote(args[i]));
            }

            ProcessStartInfo start = new ProcessStartInfo();
            start.FileName = application;
            start.WorkingDirectory = Path.GetDirectoryName(application);
            start.Arguments = arguments.ToString();
            start.UseShellExecute = false;
            // Do not modify the host registry, its environment, or other apps.
            // AyuGram itself can create host integrations if users enable them.
            Process.Start(start);
        }
        catch (Exception ex)
        {
            MessageBox.Show("Could not launch AyuGram.\n\n" + ex.Message,
                "AyuGram Portable", MessageBoxButtons.OK, MessageBoxIcon.Error);
        }
    }

    // Correct Windows command line quoting for arguments with spaces/backslashes.
    private static string Quote(string argument)
    {
        if (argument.Length == 0) return "\"\"";
        StringBuilder result = new StringBuilder("\"");
        int slashes = 0;
        foreach (char c in argument)
        {
            if (c == '\\') { ++slashes; continue; }
            if (c == '"')
            {
                result.Append('\\', slashes * 2 + 1);
                result.Append('"');
                slashes = 0;
                continue;
            }
            result.Append('\\', slashes);
            slashes = 0;
            result.Append(c);
        }
        result.Append('\\', slashes * 2);
        result.Append('"');
        return result.ToString();
    }
}
