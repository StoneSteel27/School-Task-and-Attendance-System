# attendance_system_tools/qr_code_manager.py

import io
# You'll need to install the 'qrcode' library with image support:
# pip install qrcode[pil]
import qrcode
from qrcode.image.styledpil import StyledPilImage # For more styling options if needed
from qrcode.image.styles.moduledrawers import RoundedModuleDrawer
from qrcode.image.styles.colormasks import SolidFillColorMask


class QRCodeManager:
    def __init__(self):
        """
        Initializes the QRCodeManager.
        """
        print("QRCodeManager initialized.")

    def generate_qr_code_image(
        self,
        data: str,
        image_format: str = 'PNG',
        box_size: int = 10,
        border: int = 4,
        fill_color: str = "black",
        back_color: str = "white",
        error_correction=qrcode.constants.ERROR_CORRECT_M # L, M, Q, H
    ) -> bytes:
        """
        Generates a QR code image containing the given data.

        Args:
            data: The string data to encode in the QR code.
                  (e.g., a URL, a temporary token, JSON string).
            image_format: The format of the output image (e.g., 'PNG', 'JPEG', 'SVG').
                          SVG requires qrcode[pil] and an SVGImage factory.
                          For simplicity, we'll stick to PNG for now.
            box_size: The size of each "box" in the QR code grid in pixels.
            border: The thickness of the border around the QR code (in "boxes").
            fill_color: The color of the QR code modules (the black parts).
            back_color: The background color of the QR code.
            error_correction: The error correction level.
                              qrcode.constants.ERROR_CORRECT_L (approx 7% recovery)
                              qrcode.constants.ERROR_CORRECT_M (approx 15% recovery - default)
                              qrcode.constants.ERROR_CORRECT_Q (approx 25% recovery)
                              qrcode.constants.ERROR_CORRECT_H (approx 30% recovery)

        Returns:
            bytes: The QR code image in the specified format as a byte string.

        Raises:
            ValueError: If data is empty or image_format is unsupported by basic PIL.
        """
        if not data:
            raise ValueError("Data for QR code cannot be empty.")

        supported_formats = ['PNG', 'JPEG', 'BMP', 'GIF', 'TIFF'] # Common PIL formats
        if image_format.upper() not in supported_formats:
            # For SVG, you'd use a different image_factory, e.g., qrcode.image.svg.SvgImage
            raise ValueError(f"Unsupported image format: {image_format}. Supported: {supported_formats}")

        qr = qrcode.QRCode(
            version=None,  # Automatically determine version based on data size
            error_correction=error_correction,
            box_size=box_size,
            border=border,
        )
        qr.add_data(data)
        qr.make(fit=True)

        # Create an image from the QR Code instance
        # Using PilImage for common raster formats
        img = qr.make_image(
            fill_color=fill_color,
            back_color=back_color,
            image_factory=StyledPilImage if fill_color != "black" or back_color != "white" else None # Use StyledPilImage for custom colors
        )
        # If using StyledPilImage for more advanced styling like rounded corners:
        # img = qr.make_image(
        #     image_factory=StyledPilImage,
        #     module_drawer=RoundedModuleDrawer(),
        #     color_mask=SolidFillColorMask(front_color=(R,G,B), back_color=(R,G,B)) # if needed
        # )


        # Save the image to a bytes buffer
        img_byte_buffer = io.BytesIO()
        # PIL's save method uses the format argument.
        # It's case-insensitive for common formats like 'PNG'.
        img.save(img_byte_buffer, format=image_format.upper())
        image_bytes = img_byte_buffer.getvalue()

        return image_bytes

# Example Usage (can be run directly for testing if this file is executed)
if __name__ == "__main__":
    manager = QRCodeManager()
    try:
        # Test data - in your app, this would be a unique token or URL
        test_token = "device_auth_token_123abc_for_new_login"
        qr_image_bytes = manager.generate_qr_code_image(test_token, image_format='PNG')

        # Save to a file for inspection
        with open("test_qr_code.png", "wb") as f:
            f.write(qr_image_bytes)
        print("Generated test_qr_code.png successfully.")

        # Example with different colors
        # qr_image_bytes_styled = manager.generate_qr_code_image(
        #     "Styled QR!", fill_color="darkblue", back_color="lightyellow"
        # )
        # with open("test_qr_code_styled.png", "wb") as f:
        #     f.write(qr_image_bytes_styled)
        # print("Generated test_qr_code_styled.png successfully.")

    except Exception as e:
        print(f"Error generating QR code: {e}")