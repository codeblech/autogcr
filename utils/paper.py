import random
from augraphy import *
import cv2
from pathlib import Path
import numpy as np
from PIL import Image


class PaperFaker:
    def __init__(self):
        # Initialize random values that will be used across the pipeline
        self.ink_kernel_size = random.choice([(5, 5), (3, 3)])
        self.ink_alpha = random.uniform(0.1, 0.2)
        self.letterpress_consistent_lines = random.choice([True, False])
        self.watermark_rotation = random.randint(0, 360)
        self.same_page_border = random.choice([0, 1])
        self.dirty_drum_direction = random.randint(0, 2)
        self.dirty_drum_noise_intensity = random.uniform(0.6, 0.95)
        self.dirty_drum_ksize = random.choice([(3, 3), (5, 5), (7, 7)])
        self.fold_count = random.randint(1, 4)
        self.fold_noise = random.uniform(0, 0.05)
        self.markup_type = random.choice(["strikethrough", "highlight", "underline"])
        self.blur_noise = random.choice([True, False])
        self.blur_noise_kernel = random.choice([(3, 3), (5, 5), (7, 7)])
        self.wave_pattern = random.choice([True, False])
        self.edge_effect = random.choice([True, False])
        self.fax_monochrome = random.choice([0, 1])
        self.fax_half_kernel_size = random.choice([(1, 1), (2, 2)])

    def get_realistic_page_image(self, image_path: Path) -> np.ndarray:
        """Get a realistic page from an image.

        Args:
            image_path (Path): The path to the image to make realistic.

        Returns:
            np.ndarray: The realistic page.
        """
        ink_phase = [
            # Dithering(
            #     dither=random.choice(["ordered", "floyd-steinberg"]),
            #     order=(3, 5),
            #     p=0.33,
            # ),
            InkBleed(
                intensity_range=(0.3, 0.4),
                kernel_size=self.ink_kernel_size,
                severity=(0.4, 0.5),
                # p=0.33,
            ),
            InkShifter(
                text_shift_scale_range=(18, 27),
                text_shift_factor_range=(1, 4),
                text_fade_range=(0, 2),
                noise_type="random",
            ),
            BleedThrough(
                intensity_range=(0.1, 0.3),
                color_range=(32, 224),
                ksize=(17, 17),
                sigmaX=1,
                alpha=self.ink_alpha,
                offsets=(10, 20),
                p=0.33,
            ),
            # Letterpress(
            #     n_samples=(100, 400),
            #     n_clusters=(200, 400),
            #     std_range=(500, 3000),
            #     value_range=(150, 224),
            #     value_threshold_range=(96, 128),
            #     blur=1,
            #     p=0.33,
            # ),
            # OneOf(
            #     [
            #         LowInkRandomLines(
            #             count_range=(5, 10),
            #             use_consistent_lines=self.letterpress_consistent_lines,
            #             noise_probability=0.1,
            #         ),
            #         LowInkPeriodicLines(
            #             count_range=(2, 5),
            #             period_range=(16, 32),
            #             use_consistent_lines=self.letterpress_consistent_lines,
            #             noise_probability=0.1,
            #         ),
            #     ],
            # ),
        ]

        paper_phase = [
            ColorPaper(
                hue_range=(0, 255),
                saturation_range=(10, 30),
                # p=0.33,
            ),
            # BrightnessTexturize(
            #     texturize_range=(0.9, 0.99),
            #     deviation=0.1,
            # ),
            # WaterMark(
            #     watermark_word="random",
            #     watermark_font_size=(10, 15),
            #     watermark_font_thickness=(20, 25),
            #     watermark_rotation=self.watermark_rotation,
            #     watermark_location="random",
            #     watermark_color="random",
            #     watermark_method="darken",
            #     p=0.33,
            # ),
            # OneOf(
            #     [
            #         AugmentationSequence(
            #             [
            #                 NoiseTexturize(
            #                     sigma_range=(3, 4),
            #                     turbulence_range=(2, 5),
            #                 ),
            #                 BrightnessTexturize(
            #                     texturize_range=(0.9, 0.99),
            #                     deviation=0.03,
            #                 ),
            #             ],
            #         ),
            #         AugmentationSequence(
            #             [
            #                 BrightnessTexturize(
            #                     texturize_range=(0.9, 0.99),
            #                     deviation=0.03,
            #                 ),
            #                 NoiseTexturize(
            #                     sigma_range=(3, 4),
            #                     turbulence_range=(2, 5),
            #                 ),
            #             ],
            #         ),
            #     ],
            #     p=0.33,
            # ),
            # Brightness(
            #     brightness_range=(0.9, 1.05),
            #     min_brightness=0,
            #     min_brightness_value=(120, 150),
            #     p=0.1,
            # ),
        ]

        post_phase = [
            # PageBorder(
            #     page_border_width_height="random",
            #     page_border_color=(0, 0, 0),
            #     page_border_background_color=(0, 0, 0),
            #     page_numbers="random",
            #     page_rotation_angle_range=(0, 0),
            #     curve_frequency=(2, 8),
            #     curve_height=(2, 4),
            #     curve_length_one_side=(50, 100),
            #     same_page_border=self.same_page_border,
            # ),
            Brightness(
                brightness_range=(0.9, 1.1),
                min_brightness=0,
                min_brightness_value=(120, 150),
            ),
            # DirtyDrum(
            #     line_width_range=(1, 6),
            #     line_concentration=self.dirty_drum_noise_intensity,
            #     direction=self.dirty_drum_direction,
            #     noise_intensity=self.dirty_drum_noise_intensity,
            #     noise_value=(64, 224),
            #     ksize=self.dirty_drum_ksize,
            #     sigmaX=0,
            #     p=0.33,
            # ),
            # SubtleNoise(
            #     subtle_range=random.randint(5, 10),
            #     p=0.33,
            # ),
            Jpeg(
                quality_range=(65, 95),
                # p=0.33,
            ),
            Folding(
                fold_x=None,
                fold_deviation=(0, 0),
                fold_count=self.fold_count,
                fold_angle_range=(-360, 360),
                fold_noise=self.fold_noise,
                gradient_width=(0.15, 0.5),
                gradient_height=(0.001, 0.005),
                p=0.9,
            ),
            Markup(
                num_lines_range=(2, 7),
                markup_length_range=(0.5, 1),
                markup_thickness_range=(1, 2),
                markup_type=self.markup_type,
                markup_color="random",
                single_word_mode=False,
                repetitions=1,
                p=0.33,
            ),
            # Scribbles(
            #     scribbles_type="lines",
            #     scribbles_ink="random",
            #     scribbles_location="random",
            #     scribbles_size_range=(400, 600),
            #     scribbles_count_range=(1, 6),
            #     scribbles_thickness_range=(1, 3),
            #     scribbles_brightness_change=[32, 64, 128],
            #     scribbles_skeletonize=0,
            #     scribbles_skeletonize_iterations=(2, 3),
            #     scribbles_color="random",
            #     scribbles_lines_stroke_count_range=(1, 2),
            #     p=0.33,
            # ),
            # BadPhotoCopy(
            #     noise_mask=None,
            #     noise_type=-1,
            #     noise_side="random",
            #     noise_iteration=(1, 2),
            #     noise_size=(1, 3),
            #     noise_value=(128, 196),
            #     noise_sparsity=(0.3, 0.6),
            #     noise_concentration=(0.1, 0.6),
            #     blur_noise=self.blur_noise,
            #     blur_noise_kernel=self.blur_noise_kernel,
            #     wave_pattern=self.wave_pattern,
            #     edge_effect=self.edge_effect,
            #     p=0.33,
            # ),
            Gamma(
                gamma_range=(0.9, 1.1),
                p=0.33,
            ),
            # BindingsAndFasteners(
            #     overlay_types="darken",
            #     foreground=None,
            #     effect_type="punch_holes",
            #     ntimes=(2, 6),
            #     nscales=(0.9, 1.0),
            #     edge="random",
            #     edge_offset=(10, 50),
            #     use_figshare_library=0,
            #     p=0.33,
            # ),
            # Faxify(
            #     scale_range=(0.3, 0.6),
            #     monochrome=self.fax_monochrome,
            #     monochrome_method="random",
            #     monochrome_arguments={},
            #     halftone=random.choice([0, 1]),
            #     invert=1,
            #     half_kernel_size=self.fax_half_kernel_size,
            #     angle=(0, 360),
            #     sigma=(1, 3),
            #     p=0.33,
            # ),
        ]

        pipeline = AugraphyPipeline(
            ink_phase=ink_phase, paper_phase=paper_phase, post_phase=post_phase
        )
        image = cv2.imread(image_path)
        augmented_image = pipeline(image)
        return augmented_image

    def get_realistic_page_images(self, image_paths: list[Path]) -> list[np.ndarray]:
        """Get a list of realistic pages from a list of images.

        Args:
            image_paths (list[Path]): The paths to the images to make realistic.

        Returns:
            list[np.ndarray]: A list of realistic pages.
        """
        pages = []
        for image_path in image_paths:
            pages.append(self.get_realistic_page_image(image_path))
        return pages

    def get_realistic_pages_pdf(
        self, image_paths: list[Path], output_file_path: Path
    ) -> bool:
        """Get a PDF with realistic pages.

        Args:
            image_paths (list[Path]): The paths to the images to make realistic.

        Returns:
            bool: True if the PDF was created successfully, False otherwise.
        """
        pages = self.get_realistic_page_images(image_paths)
        images: list[Image.Image] = []
        for arr in pages:
            if arr.ndim == 2:
                # Grayscale -> convert to RGB
                arr = np.stack([arr] * 3, axis=-1)
            elif arr.shape[2] == 4:
                # Drop alpha channel if present
                arr = arr[:, :, :3]
            pil_img = Image.fromarray(arr.astype(np.uint8)).convert("RGB")
            images.append(pil_img)
        if images:
            images[0].save(output_file_path, save_all=True, append_images=images[1:])
            return True
        else:
            return False
