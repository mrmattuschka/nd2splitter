import argparse
import warnings
from os import makedirs
from pathlib import Path

from nd2reader import ND2Reader
from skimage.io import imsave
from skimage.util import img_as_ubyte
from tqdm import tqdm
from numpy import uint8


def main():

    parser = argparse.ArgumentParser(
        description="Splitting & conversion of images from .nd2 to .tiff format"
    )

    parser.add_argument(
        "-i", 
        "--input",
        required=True
    )
    parser.add_argument(
        "-o",
        "--output",
        default=False,
        help="if no output directory is given, output will be written to the input directory"
    )
    parser.add_argument(
        "-a",
        "--axes",
        default="v",
        help="names of axes along which the images shall be split (default: v)"
    )
    parser.add_argument(
        "-r",
        "--recursive",
        action="store_true",
        help="include files in subdirectories"
    )
    parser.add_argument(
        "-s",
        "--squeeze",
        action="store_true",
        help="when using recursive mode, don't recreate input structure but instead include subdir names in file name"
    )
    parser.add_argument(
        "-f",
        "--format",
        choices=["tif", "png", "jpg"],
        default="tif",
        help="output format to convert images to. Png and jpg format will result in image stacks being split along all axes (default: tif)"
    )

    args = parser.parse_args()

    input_path = Path(args.input)
    output_path = Path(args.output) if args.output else Path(args.input)
    split_axes = list(args.axes)

    images = list(input_path.glob(f"{'**' if args.recursive else '.'}/*.nd2"))

    if args.format in ["png", "jpg"]:
        warnings.filterwarnings("ignore", category=UserWarning)

    print(f"Converting {len(images)} images...")

    for filename in tqdm(images):
        if args.recursive & args.squeeze:
            img_output_basepath = Path(output_path, "_".join(filename.relative_to(input_path).parts))
        else:
            img_output_basepath = Path(output_path, filename.relative_to(input_path))
        makedirs(img_output_basepath.parent, exist_ok=True)
        
        image = ND2Reader(filename)

        if args.format == "tif":
            image.iter_axes = [ax for ax in split_axes if ax in image.axes]
            image.bundle_axes = [ax for ax in image.axes[::-1] if ax not in image.iter_axes]
        else:
            image.iter_axes = [ax for ax in image.axes if ax not in "xy"]
            image.bundle_axes = "yx"
        
        for split_image in image:
            metadata = split_image.metadata.copy()
            metadata["date"]   = str(metadata["date"])
            metadata["coords"] = {key: int(val) for key, val in metadata["coords"].items()}

            coords_str = "_".join([f"{key}-{val}" for key, val in metadata["coords"].items()])
            img_output_path = img_output_basepath.with_name(img_output_basepath.name + "_" + coords_str + "." + args.format)
            if args.format in ["png", "jpg"]:
                imsave(str(img_output_path), img_as_ubyte(split_image), check_contrast=False)
            else:
                imsave(str(img_output_path), split_image, check_contrast=False, metadata=metadata)


if __name__ == "__main__":
    main()
