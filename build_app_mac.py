#!/usr/bin/env python3
import os
import sys
import subprocess
import tempfile
import shutil
from pathlib import Path

# Use a permanent folder in the project for the Matplotlib cache instead of /tmp
mpl_cache = os.path.join(os.getcwd(), "mplcache")
os.makedirs(mpl_cache, exist_ok=True)
print(f"Prebuilding matplotlib font cache in {mpl_cache} ...")
# Pre-build the font cache by importing matplotlib; this builds and saves the cache in mplcache
subprocess.run([sys.executable, "-c", "import matplotlib.pyplot as plt; plt.figure()"], check=True)
# Set MPLCONFIGDIR for the current process
os.environ["MPLCONFIGDIR"] = mpl_cache
print(f"Set MPLCONFIGDIR to {mpl_cache}")

# Increase recursion limit for the local Python process
sys.setrecursionlimit(10000)

def main():
    """Build CART-GUI application using PyInstaller with appropriate settings."""
    print("Building CART-GUI application...")
    
    # Create a temporary runtime hook to increase recursion limit and set MPLCONFIGDIR for the bundled app
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as hook_file:
        hook_path = hook_file.name
        hook_file.write("import sys\n")
        hook_file.write("sys.setrecursionlimit(10000)\n")
        # Set MPLCONFIGDIR in the bundled app to the bundled mplcache folder
        hook_file.write("import os\n")
        hook_file.write("os.environ['MPLCONFIGDIR'] = 'mplcache'\n")
        hook_file.write("print('PyInstaller: Recursion limit increased and MPLCONFIGDIR set to mplcache')\n")
    
    # Create a PyQt5 hook to fix Qt library paths
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as qt_hook_file:
        qt_hook_path = qt_hook_file.name
        qt_hook_file.write("import os\n")
        qt_hook_file.write("import sys\n")
        qt_hook_file.write("import PyQt5\n\n")
        qt_hook_file.write("# Add PyQt5 binary directory to PATH to help find Qt libraries\n")
        qt_hook_file.write("pyqt_dir = os.path.dirname(PyQt5.__file__)\n")
        qt_hook_file.write("os.environ['PATH'] = os.path.join(pyqt_dir, 'Qt5', 'bin') + os.pathsep + os.environ['PATH']\n")
        qt_hook_file.write("# Set QT_PLUGIN_PATH environment variable\n")
        qt_hook_file.write("os.environ['QT_PLUGIN_PATH'] = os.path.join(pyqt_dir, 'Qt5', 'plugins')\n")
    
    print(f"Created runtime hook at {hook_path}")
    print(f"Created PyQt5 hook at {qt_hook_path}")
    
    # Define the PyInstaller command; note the addition of the mplcache folder as data
    cmd = [
        "pyinstaller",
        "--name=CART-GUI",
        "--windowed",
        "--clean",
        f"--runtime-hook={hook_path}",
        f"--runtime-hook={qt_hook_path}",
        "--icon=docs/images/main_gui.png",
        "--add-data=docs/images:docs/images",
        # Include the mplcache folder so the bundled app has a pre-built font cache
        f"--add-data={mpl_cache}{os.pathsep}mplcache",
        "--collect-all=PyQt5",
        "--hidden-import=pandas",
        "--hidden-import=numpy",
        "--hidden-import=matplotlib",
        "--hidden-import=scipy",
        "--hidden-import=scipy.stats",
        "--hidden-import=scipy.spatial.distance",
        "--hidden-import=scipy.stats.mstats",
        "--hidden-import=sklearn",
        "--hidden-import=sklearn.manifold",
        "--hidden-import=sklearn.preprocessing",
        "--hidden-import=pingouin",
        "--hidden-import=matplotlib.backends.backend_qt5agg",
        "--hidden-import=PyQt5",
        "--hidden-import=PyQt5.QtCore",
        "--hidden-import=PyQt5.QtGui",
        "--hidden-import=PyQt5.QtWidgets",
        "srt_analysis_deluxe_GUI.py"
    ]
    
    # Insert macOS-specific options if on darwin
    if sys.platform == 'darwin':
        icns_path = "/Users/David/Documents/GitHub/Simple_SRT/Analysis/AppIcon.icns"
        if not os.path.exists(icns_path):
            print(f"Warning: {icns_path} not found. App will have default icon.")
            print("To create an ICNS file from PNG, see instructions in BUILD_INSTRUCTIONS.md")
        else:
            cmd.insert(5, f"--osx-bundle-identifier=org.cart-gui")
            cmd.insert(5, f"--icon={icns_path}")
    
    print("Running PyInstaller with the following command:")
    print(" ".join(cmd))
    print("\nThis may take several minutes...\n")
    
    result_code = 0
    try:
        subprocess.run(cmd, check=True)
        print("\nBuild completed successfully!")
        print("The application can be found in the 'dist' directory.")
        
        # Automatically fix Qt library rpaths in the bundle on macOS
        if sys.platform == 'darwin':
            fix_macos_bundle()
        
    except subprocess.CalledProcessError as e:
        print(f"\nBuild failed with error code {e.returncode}")
        print("See the output above for more details.")
        result_code = e.returncode
    finally:
        # Clean up the temporary hook files
        try:
            os.unlink(hook_path)
            os.unlink(qt_hook_path)
            print("Removed temporary hook files")
        except Exception as e:
            print(f"Could not remove temporary hook files: {e}")
    
    return result_code

def fix_macos_bundle():
    """Perform post-processing fixes on the macOS bundle to adjust Qt library rpaths."""
    app_path = Path('dist/CART-GUI.app')
    frameworks_dir = app_path / 'Contents' / 'Frameworks'
    
    print("\nPerforming post-build fixes on macOS bundle...")
    try:
        # Create a folder for Qt libraries if it does not exist
        qt_libs_dir = frameworks_dir / 'Qt'
        if not qt_libs_dir.exists():
            qt_libs_dir.mkdir(exist_ok=True)
            print(f"Created {qt_libs_dir}")
        
        # Move any Qt libraries from Frameworks that start with 'Qt' into the Qt folder
        for qt_file in frameworks_dir.glob('Qt*'):
            if qt_file.is_file():
                target = qt_libs_dir / qt_file.name
                if not target.exists():
                    shutil.move(str(qt_file), str(target))
                    print(f"Moved {qt_file.name} to {target}")
        
        # Create symlinks in the Frameworks directory for the Qt libraries from the Qt folder
        for target_file in qt_libs_dir.iterdir():
            symlink_path = frameworks_dir / target_file.name
            if not symlink_path.exists():
                os.symlink(target_file, symlink_path)
                print(f"Created symlink: {symlink_path} -> {target_file}")
        
        # Fix rpaths in PyQt5 libraries (e.g., QtWidgets.abi3.so) if they refer to @rpath/QtWidgets
        pyqt5_dir = frameworks_dir / "PyQt5"
        if pyqt5_dir.exists():
            for so_file in pyqt5_dir.glob("*.so*"):
                try:
                    otool_output = subprocess.check_output(["otool", "-L", str(so_file)]).decode()
                    if "@rpath/QtWidgets" in otool_output:
                        new_path = "@executable_path/../Frameworks/Qt/QtWidgets"
                        subprocess.run(["install_name_tool", "-change", "@rpath/QtWidgets", new_path, str(so_file)], check=True)
                        print(f"Fixed rpath for {so_file.name}: @rpath/QtWidgets -> {new_path}")
                except Exception as e:
                    print(f"Error processing {so_file.name}: {e}")
        else:
            print("No PyQt5 directory found in Frameworks; skipping rpath fixes for PyQt5 libraries.")
        
        print("macOS bundle post-processing completed.")
    except Exception as e:
        print(f"Error during bundle post-processing: {e}")

if __name__ == "__main__":
    sys.exit(main())