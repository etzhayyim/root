import os
import shutil
import subprocess

apps_dir = "60-apps"
if not os.path.exists(apps_dir):
    print(f"{apps_dir} not found.")
    exit(0)

for item in os.listdir(apps_dir):
    if item.startswith("etzhayyim-"):
        # Determine the target name
        target_item = item.replace("etzhayyim-", "etzhayyim-")
        src_path = os.path.join(apps_dir, item)
        dst_path = os.path.join(apps_dir, target_item)
        
        if os.path.exists(dst_path):
            print(f"Merge {src_path} into {dst_path}")
            # Merge contents using rsync
            subprocess.run(["rsync", "-a", f"{src_path}/", f"{dst_path}/"], check=True)
            shutil.rmtree(src_path)
        else:
            print(f"Rename {src_path} to {dst_path}")
            os.rename(src_path, dst_path)
