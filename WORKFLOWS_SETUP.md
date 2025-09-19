# GitHub Actions Setup Instructions

## How to Enable Automated Builds

The GitHub Actions workflows have been created but need to be pushed manually due to permission restrictions.

### Option 1: Push from Terminal

```bash
git push origin feature/gui-improvements
```

### Option 2: Manual Setup

1. Go to your GitHub repository
2. Click on "Actions" tab
3. Click "New workflow"
4. Copy the content from `.github/workflows/build-executables.yml`
5. Paste and commit directly on GitHub

## How the Workflows Work

### Automatic Release Builds

When you create a new tag (e.g., `v2.0.0`), the workflow will:

1. Build executables for Windows, macOS, and Linux
2. Create a GitHub Release
3. Attach all executables as downloadable ZIP files

To trigger:
```bash
git tag v2.0.0
git push origin v2.0.0
```

### Manual Test Builds

The test workflow runs on every push to test that builds work correctly.

### Manual Trigger

You can also trigger builds manually from the GitHub Actions tab.

## Local Building

To build locally, run:
```bash
python build_all.py
```

This will create a platform-specific executable in the `dist` folder.

## Workflow Features

- **Multi-platform support**: Windows (.exe), macOS (.app), Linux
- **Automatic versioning**: Based on git tags
- **Hidden imports included**: All necessary tkinter and PIL modules
- **Standalone executables**: No Python installation required
- **Automatic release creation**: With downloadable artifacts

## Requirements for Users

Users downloading the executables don't need any prerequisites - the executables are completely standalone!

## Authors

Lorenzo Cardarelli and Enzo Cocca

## License

Apache License 2.0