# winget manifest

Templates to publish Auris on the Windows Package Manager
([microsoft/winget-pkgs](https://github.com/microsoft/winget-pkgs)). Once merged,
anyone can install with:

```powershell
winget install Abrahao.Auris
```

## How to submit a new version

1. Publish the release so `AurisSetup.exe` is available at the `InstallerUrl`.
2. Get the installer hash:
   ```powershell
   winget hash .\AurisSetup.exe      # or: (Get-FileHash AurisSetup.exe).Hash
   ```
3. In the three yaml files, bump `PackageVersion`, update the `InstallerUrl`
   version, and paste the hash into `InstallerSha256`.
4. Fork `microsoft/winget-pkgs` and place the files under
   `manifests/a/Abrahao/Auris/<version>/`, then open a PR. Validate first with:
   ```powershell
   winget validate --manifest <folder>
   ```
