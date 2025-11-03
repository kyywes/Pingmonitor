# PingMonitor Pro v2.0 - Installer Creation Guide

## 🎯 Two Options for Distribution

### Option 1: Professional Windows Installer (Recommended)
Creates a `.exe` installer like Node.js, Visual Studio Code, etc.

**Requirements:**
- Inno Setup 6.x ([Download here](https://jrsoftware.org/isdl.php))

**Steps:**
1. Install Inno Setup 6
2. Navigate to `installer/` folder
3. Run `BUILD_INSTALLER.bat`
4. Installer will be created in `dist/PingMonitorPro_v2_Setup.exe`

**Features:**
- ✅ Professional wizard interface
- ✅ Automatic Python dependency installation
- ✅ Desktop shortcut creation
- ✅ Start menu integration
- ✅ Windows startup option
- ✅ Clean uninstaller
- ✅ Firewall configuration

**Distribution:**
- Share the `PingMonitorPro_v2_Setup.exe` file
- Users just double-click and follow the wizard
- All dependencies installed automatically

---

### Option 2: Portable ZIP Package
Creates a ZIP file that users can extract and run.

**Requirements:**
- Python 3.8+ (already have it!)

**Steps:**
1. Run `python create_portable.py` from project root
2. ZIP file created in `dist/PingMonitorPro_v2_Portable_YYYYMMDD.zip`

**Features:**
- ✅ No installer required
- ✅ Extract and run
- ✅ Portable - can run from USB drive
- ✅ Includes installation instructions

**Distribution:**
- Share the ZIP file
- Users extract to a folder
- Run `START.bat` to launch

---

## 📦 What Gets Packaged

Both options include:
- Main application (`PingMonitorPro.pyw`)
- All source code (`src/`)
- Configuration (`config/`)
- Documentation (README, guides)
- Icon files
- Launch scripts

---

## 🚀 Which Option to Choose?

**Use Professional Installer if:**
- You want maximum professionalism
- Target audience is non-technical
- Want automatic dependency installation
- Need Start menu / Desktop shortcuts
- Want uninstaller

**Use Portable ZIP if:**
- You want quick distribution
- Don't want to install Inno Setup
- Target audience is technical
- Want portable installation (USB drive, etc.)
- Quick testing/deployment

---

## 📋 Testing the Installer

Before distributing:

1. **Test on clean VM/PC:**
   - Fresh Windows installation
   - Python 3.8+ installed
   - Run installer/extract ZIP
   - Verify app launches correctly

2. **Test all features:**
   - Device monitoring
   - Email alerts
   - SSH terminal
   - Context menus
   - Email test

3. **Test uninstallation** (for .exe installer):
   - Uninstall via Windows Settings
   - Verify clean removal

---

## 🛠️ Customization

### For Inno Setup Installer:
Edit `installer/setup_script.iss`:
- Change app name/version
- Modify installation options
- Add/remove components
- Customize wizard pages

### For Portable Package:
Edit `create_portable.py`:
- Add/remove files
- Modify installation instructions
- Change ZIP compression

---

## 📝 Notes

- **Python requirement:** Both options require Python 3.8+ on target machine
- **Dependencies:** Installer auto-installs, portable requires manual `pip install`
- **Size:** Installer ~2-5 MB, Portable ZIP ~1-3 MB
- **Updates:** Create new installer/ZIP for each version

---

## ✅ Checklist Before Distribution

- [ ] Tested on clean Windows machine
- [ ] All features working
- [ ] Documentation up to date
- [ ] Version number updated
- [ ] config.json has correct values
- [ ] Icon files present
- [ ] No debug code/credentials in files
- [ ] LICENSE.txt included

---

## 🎉 Ready to Distribute!

After building, you'll have a professional installer ready to share!

For support or questions, check the main README.md or documentation files.
