import pandas as pd
import os
from PIL import Image
import numpy as np
import matplotlib.pyplot as plt
import cv2
from tabulate import tabulate
from skimage.measure import shannon_entropy
from src.defs import IMAGE_DIRECTORIES as imdir, DiseaseCategory as dc, ImageType as it


class ImageProcessor():
    
    # class provides methods to prepare the images for modelling
    
    def __init__(self):
        pass
    
    def loadImgs(self, imgNames, from_dir):
        """
        loads images by file names like 'Viral Pneumonia-101.png' from a directory

        params: imgNames is a list with file names
        returns: a tuple with loaded images and a tuple with corresponding image names
        """
        imgs = []
                
        if not imgNames:
            raise Exception("provide a list with image names including the extension")
        
        for iname in imgNames: 
            
            # determine image path
            fileDir = from_dir
            filePath = fileDir+rf"\{iname}"
            if os.path.exists(filePath):
                img = cv2.imread(filePath, cv2.IMREAD_GRAYSCALE)
                imgs.append(img)
            else:
                raise Exception(f"file {iname} not found in {fileDir}")

        
            
        return tuple(imgs), tuple(imgNames)



    def plot_images(self, images, titles=None, tSize=10, max_img_per_row=5):
        
        import math 
        
        num_images = len(images)
        #cols = min(5, num_images)  # Maximum 5 images per row
        cols = min(max_img_per_row, num_images)  # Maximum 4 images per row
        rows = math.ceil(num_images / cols)  # Calculate required rows

        fig_width = cols * 4  # Set width dynamically (4 inches per image)
        fig_height = rows * 4  # Set height dynamically (4 inches per row)

        fig, axes = plt.subplots(rows, cols, figsize=(fig_width, fig_height))

        # Flatten axes array if there's more than one row
        if rows > 1:
            axes = axes.flatten()
        else:
            axes = [axes] if num_images == 1 else axes

        for i, img in enumerate(images):
            axes[i].imshow(img, cmap='gray')  # Display image (adjust cmap as needed)
            if titles:
                axes[i].set_title(titles[i], fontsize=tSize)
            axes[i].axis("off")  # Hide axes

        # Hide unused subplots
        for j in range(i + 1, len(axes)):
            axes[j].axis("off")

        plt.tight_layout()
        plt.show()
        
    
    
    def downscale(self, img, new_size, interpolation=cv2.INTER_AREA, plotResult=True):
        # resizes a gray-scaled image to the new_size and returns
              
        # Resize using INTER_AREA
        downscaled_image = cv2.resize(img, new_size, interpolation=interpolation)

        if plotResult:
            try :
                # Display the original and overlay images
                plt.title(f"Downscaled image {new_size}")
                plt.imshow(downscaled_image)
                plt.axis('off')
                plt.show()  
            except:
                pass
        
        return downscaled_image



    def downscaleToFolder(self, inputFolder, outputFolder, new_size, interpolation=cv2.INTER_AREA, debug=True):
        
        # get image names
        filenames = os.listdir(inputFolder)  # Returns a list of filenames
        
        # load images
        imgs, iNames = self.loadImgs(imgNames=filenames, from_dir=inputFolder)
        
        # size str
        sz = f"{new_size[0]}x{new_size[1]}"
        
        # subfolder with size
        
        outputFolder_HxW = os.path.join(outputFolder, sz)
        
        # create directory
        os.makedirs(outputFolder_HxW, exist_ok=True)
        
        cnt = 0

        # downscale and save
        for img, name in zip(imgs, iNames):
            
            cnt += 1
            
            dImg = self.downscale(img, new_size, interpolation, plotResult=False)
            fName = rf"\{new_size[0]}x{new_size[1]}_{name}"
            file_path = outputFolder_HxW+fName
            cv2.imwrite(file_path, dImg)
            
        
        if debug:
            print(f"{cnt} images have been downscaled and stored to {outputFolder_HxW}")       
            
              
    
  
    def getRoiWithResizedMask(self, img, mask, contourThiknes=1, plotResult=True):
        # Resize the mask to match the X-ray image size and returns the original image 
        # overlayed with mask contour 
        
        # Resize the mask to match the X-ray image size
        resized_mask = cv2.resize(mask, (img.shape[1], img.shape[0]), interpolation=cv2.INTER_LINEAR)

        # Find contours from the resized mask
        contours, _ = cv2.findContours(resized_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        # Create a copy of the X-ray image for overlay
        overlay_image = img.copy()

        # Draw contours on the overlay image in red (BGR: (0, 0, 255))
        cv2.drawContours(overlay_image, contours, -1, (0, 0, 255), thickness=contourThiknes)

        # Convert images to RGB for matplotlib visualization
        img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        overlay_image_rgb = cv2.cvtColor(overlay_image, cv2.COLOR_BGR2RGB)
        
        
        # Create a binary mask for the contour area
        binary_mask = cv2.drawContours(
            np.zeros_like(resized_mask, dtype=np.uint8),  # Blank canvas
            contours,
            -1,
            (255),  # White color for contours
            thickness=contourThiknes
        )

        # Fill the contours to include the area inside
        filled_mask = cv2.drawContours(
            binary_mask,
            contours,
            -1,
            (255),  # White color for filling
            thickness=cv2.FILLED
        )

        # Apply the mask to the original image
        lung_area = cv2.bitwise_and(img, img, mask=filled_mask)


        if plotResult:
            try :
                # Display the original and overlay images
                plt.figure(figsize=(15, 5))
                plt.subplot(1, 4, 1)
                plt.title("Original X-ray (299x299)")
                plt.imshow(img_rgb)
                plt.axis('off')
                
                plt.subplot(1, 4, 2)
                plt.title("Resized mask (299x299)")
                plt.imshow(resized_mask)
                plt.axis('off')

                plt.subplot(1, 4, 3)
                plt.title("X-ray with Mask's contours")
                plt.imshow(overlay_image_rgb)
                plt.axis('off')
                
                plt.subplot(1, 4, 4)
                plt.title("Region of interest (ROI) inc. contour")
                plt.imshow(lung_area)
                plt.axis('off')

                plt.tight_layout()
                plt.show()  
                
            except:
                pass
        
        return lung_area




# Analyze class distribution
def class_distribution(image_directories):
    class_counts = {category: len(os.listdir(paths["images"])) for category, paths in image_directories.items()}
    plt.bar(class_counts.keys(), class_counts.values(), color='green')
    plt.title('Class Distribution')
    #plt.xlabel('Category')
    plt.ylabel('Number of Images')
    plt.show()
    

def get_image_metadata(image_directory):
    # Dictionary to store image properties
    image_metadata = {}

    # Iterate through all .png images in the directory
    all_images = [img for img in os.listdir(
        image_directory) if img.endswith('.png')]

    for image_name in all_images:
        image_path = os.path.join(image_directory, image_name)

        # Read the image
        image = cv2.imread(image_path)
        if image is None:
            print(f"Warning: Could not read image {image_name}")
            continue

        # Get resolution (height, width, channels)
        height, width = image.shape[:2]

        # Determine color property
        if len(image.shape) == 3 and image.shape[2] == 3:
            color_property = "RGB"
        else:
            color_property = "grey"

        # Add to dictionary
        image_metadata[image_name] = [f"{width}x{height}", color_property]

    return image_metadata


def img_data_overview(image_directories):
    data = []
    # "Check for completeness of images, masks, and masked images."
    # Initialize counters for Images, Masks, and Masked
    total_counts = [0, 0, 0]

    for key, value in image_directories.items():
        cnts = []
        for k, folder_path in value.items():
            count = len(os.listdir(folder_path))
            cnts.append(count)

        # Add counts for the current category to the total
        total_counts = [total_counts[i] + cnts[i] for i in range(len(cnts))]

        # Append category-specific data
        data.append([key] + cnts)

    # Append totals to the data
    data.append(["Total"] + total_counts)

    # Headers
    headers = ["Category", "Images", "Masks", "Masked"]

    # Print side by side
    print(tabulate(data, headers=headers, tablefmt="grid"))


def img_count(categories, image_directories):
    # Use specified categories or all by default
    cntDict = {}
    for category in categories:
        image_directory = image_directories[category]["images"]
        # Count the number of images in each directory
        cntDict[category] = len([img for img in os.listdir(
            image_directory) if img.endswith('.png')])

    return cntDict


def has_black_frame(image, threshold=10):
    """Check if the image has a black frame around it."""
    height, width = image.shape[:2]

    # Extract borders
    top_border = image[:threshold, :]
    bottom_border = image[-threshold:, :]
    left_border = image[:, :threshold]
    right_border = image[:, -threshold:]

    # Combine all borders
    borders = np.concatenate((top_border.flatten(), bottom_border.flatten(
    ), left_border.flatten(), right_border.flatten()))

    # If most border pixels are black, return True
    return np.mean(borders) < 10


def calculate_blurriness(image):
    # Variance of Laplacian method for blurriness detection
    return cv2.Laplacian(image, cv2.CV_64F).var()


def calculate_contrast(image):
    # Contrast calculated as the difference between max and min pixel intensities
    return image.max() - image.min()


def calculate_variance(image):
    # Variance of pixel intensities
    return np.var(image)


def calculate_entropy(image):
    # Entropy calculation using skimage.measure.shannon_entropy
    return shannon_entropy(image)


def get_greyscale_image_metrics(directory):
    # List to store image properties
    image_metrics = []

    # Iterate through all images in the directory
    all_images = [img for img in os.listdir(
        directory) if img.endswith('.png') or img.endswith('.jpg')]

    for image_name in all_images:
        image_path = os.path.join(directory, image_name)

        # Load the image in greyscale
        image = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
        if image is None:
            print(f"Warning: Could not read image {image_name}")
            continue

        # Calculate image metrics
        mean_intensity = np.mean(image)
        variance = calculate_variance(image)
        blurriness = calculate_blurriness(image)
        contrast = calculate_contrast(image)
        entropy = calculate_entropy(image)

        # Append properties to the list
        image_metrics.append({
            "file name": image_name.strip(".png"),
            "mean intensity": mean_intensity,
            "variance": variance,
            "blurriness": blurriness,
            "contrast": contrast,
            "entropy": entropy
        })

    # Convert list to DataFrame
    df = pd.DataFrame(image_metrics)

    return df


def rename_masks(masks_dir):
    # Iterate through all files in the directory
    for filename in os.listdir(masks_dir):
        if filename.startswith("m"):  # already renamed
            continue
        else:
            # Construct the old and new file paths
            old_path = os.path.join(masks_dir, filename)
            new_filename = f"m{filename}"
            new_path = os.path.join(masks_dir, new_filename)

            # Rename the file
            os.rename(old_path, new_path)
            print(f"Renamed: {filename} -> {new_filename}")


def apply_masks(imgs_dir, masks_dir, output_dir):
    if not os.path.exists(imgs_dir):
        raise FileNotFoundError(f"Images directory does not exist: {imgs_dir}")
    if not os.path.exists(masks_dir):
        raise FileNotFoundError(f"Masks directory does not exist: {masks_dir}")

    for img_file in os.listdir(imgs_dir):
        # Construct paths for image and mask
        img_path = os.path.join(imgs_dir, img_file)
        mask_file = "m" + img_file  # Assuming masks start with 'm'
        mask_path = os.path.join(masks_dir, mask_file)

        # Check if image and mask exist
        if not os.path.exists(img_path):
            print(f"Image file not found: {img_path}")
            continue
        if not os.path.exists(mask_path):
            print(f"Mask file not found: {mask_path}")
            continue

        # Load the image and mask
        image = Image.open(img_path).convert("L")  # Grayscale image
        mask = Image.open(mask_path).convert("L")  # Grayscale mask

        # Resize mask if necessary
        if image.size != mask.size:
            mask = mask.resize(image.size, Image.NEAREST)

        # Apply the mask
        image_array = np.array(image)
        mask_array = np.array(mask)
        masked_image_array = image_array * \
            (mask_array > 0)  # Keep only masked regions

        # Ensure the output directory exists
        # if exists: does noting, else: creates one
        os.makedirs(output_dir, exist_ok=True)

        # Save the masked image
        masked_image = Image.fromarray(masked_image_array.astype('uint8'), "L")
        masked_file_name = "mskd_"+img_file
        output_path = os.path.join(output_dir, masked_file_name)
        masked_image.save(output_path)

        print(f"Processed and saved: {output_path}")


# Rename files by prepending the prefix "mskd"
def rename_files_with_prefix(directory, prefix):
    if not os.path.exists(directory):
        raise FileNotFoundError(f"The directory does not exist: {directory}")

    for file_name in os.listdir(directory):
        old_file_path = os.path.join(directory, file_name)

        # Skip if it's not a file
        if not os.path.isfile(old_file_path):
            continue

        # Create new file name with prefix
        new_file_name = f"{prefix}{file_name}"
        new_file_path = os.path.join(directory, new_file_name)

        # Rename the file
        os.rename(old_file_path, new_file_path)
        print(f"Renamed: {old_file_path} -> {new_file_path}")


def visualize_random_images(image_paths, n_samples_per_category=5):
    """
    Visualize random samples of images from each category.

    Args:
        image_paths (list of tuples): List of tuples with (category, path) pairs.
        n_samples_per_category (int): Number of random samples to visualize per category.
    """
    # Group images by category
    category_dict = {}
    for category, path in image_paths:
        if category not in category_dict:
            category_dict[category] = []
        category_dict[category].append(path)

    # Visualize
    n_categories = len(category_dict)
    fig, axes = plt.subplots(
        n_categories, n_samples_per_category, figsize=(20, 4 * n_categories))

    if n_categories == 1:
        axes = [axes]  # Ensure axes is iterable when there is only one category

    for row, (category, paths) in enumerate(category_dict.items()):
        sampled_paths = np.random.choice(
            paths, size=n_samples_per_category, replace=False)
        for col, path in enumerate(sampled_paths):
            img = Image.open(path).convert('L')  # Convert to grayscale
            axes[row][col].imshow(img, cmap='gray')
            axes[row][col].set_title(category)
            axes[row][col].axis('off')

    plt.tight_layout()
    plt.show()
