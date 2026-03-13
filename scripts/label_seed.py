import cv2
import os
import shutil

seed_folder = r"C:\Users\abick\OneDrive\Desktop\capstoneProject\data\seed"

spiral_folder = os.path.join(seed_folder, 'spiral')
elliptical_folder = os.path.join(seed_folder, 'elliptical')
irregular_folder = os.path.join(seed_folder, 'irregular')

os.makedirs(spiral_folder, exist_ok=True)
os.makedirs(elliptical_folder, exist_ok=True)
os.makedirs(irregular_folder, exist_ok=True)

images = [f for f in os.listdir(seed_folder) if f.lower().endswith(('.jpg', '.jpeg', '.png'))]

print(f"Found {len(images)} images to label.")

for img_file in images:
    img_path = os.path.join(seed_folder, img_file)
    
    # Load and show image
    img = cv2.imread(img_path)
    cv2.imshow("Galaxy - Press 's' for Spiral, 'e' for Elliptical", img)
    
    # Wait for keypress
    key = cv2.waitKey(0) & 0xFF
    
    # Move image based on keypress
    if key == ord('s'):
        shutil.move(img_path, os.path.join(spiral_folder, img_file))
    elif key == ord('e'):
        shutil.move(img_path, os.path.join(elliptical_folder, img_file))
    
    # Close the window for next image
    cv2.destroyAllWindows()

print("Labeling complete!")