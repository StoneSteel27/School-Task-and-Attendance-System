# attendance_system_tools/recovery_codes_manager.py

import secrets
import string
import hashlib
from typing import List, Set


class RecoveryCodesManager:
    def __init__(
            self,
            num_segments: int = 3,
            segment_length: int = 5,
            separator: str = '-',
            # Character set: Alphanumeric, excluding visually similar characters (0/O, 1/I/L).
            # Using uppercase for better readability and less user error.
            character_set: str = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"  # 32 chars, 5 bits entropy per char
    ):
        """
        Initializes the RecoveryCodesManager with formatting options for the codes.

        Args:
            num_segments: How many segments the code should have (e.g., 3 for XXXX-XXXX-XXXX).
            segment_length: The length of each segment.
            separator: The character used to separate segments.
            character_set: The pool of characters to use for generating codes.
                           Defaults to a set that excludes common ambiguous characters.
        """
        if num_segments <= 0 or segment_length <= 0:
            raise ValueError("Number of segments and segment length must be positive.")
        if not character_set:
            raise ValueError("Character set cannot be empty.")
        if separator in character_set:
            raise ValueError(f"Separator '{separator}' cannot be part of the character set.")

        self.num_segments = num_segments
        self.segment_length = segment_length
        self.separator = separator
        self.character_set = character_set
        self.expected_normalized_length = self.num_segments * self.segment_length
        print(
            f"RecoveryCodesManager initialized: "
            f"{self.num_segments} segments of {self.segment_length} chars, "
            f"separated by '{self.separator}'. "
            f"Total code entropy: approx {self.expected_normalized_length * (len(self.character_set).bit_length() - 1)} bits."
        )

    def _normalize_code(self, code_string: str) -> str:
        """
        Normalizes a recovery code string by removing separators and converting to uppercase.
        This is used internally before hashing or validation.
        """
        return code_string.replace(self.separator, "").upper()

    def generate_recovery_codes(self, count: int = 10) -> List[str]:
        """
        Generates a specified number of unique, formatted recovery codes.
        These are the plain-text codes to be shown to the user once.

        Args:
            count: The number of recovery codes to generate.

        Returns:
            A list of plain text recovery codes, formatted for display.

        Raises:
            ValueError: If count is not positive.
            RuntimeError: If unable to generate enough unique codes (highly unlikely with good params).
        """
        if count <= 0:
            raise ValueError("Number of codes to generate must be positive.")

        generated_formatted_codes: Set[str] = set()
        plain_text_codes_for_user: List[str] = []

        # Max attempts to prevent an infinite loop in the unlikely event of many collisions.
        max_attempts = count * 5  # Allow some leeway

        for attempt in range(max_attempts):
            if len(plain_text_codes_for_user) >= count:
                break

            segments: List[str] = []
            for _ in range(self.num_segments):
                segment = "".join(secrets.choice(self.character_set) for _ in range(self.segment_length))
                segments.append(segment)

            formatted_code = self.separator.join(segments)

            # Ensure uniqueness of the formatted code
            if formatted_code not in generated_formatted_codes:
                generated_formatted_codes.add(formatted_code)
                plain_text_codes_for_user.append(formatted_code)

        if len(plain_text_codes_for_user) < count:
            raise RuntimeError(
                f"Could not generate enough unique recovery codes. "
                f"Only generated {len(plain_text_codes_for_user)} out of {count} requested. "
                f"Check parameters (character set size, code length, requested count)."
            )

        return plain_text_codes_for_user

    def get_code_hash(self, code_string: str) -> str:
        """
        Validates and hashes a given recovery code string.
        The code is first normalized (separators removed, uppercased).
        The normalized code is then validated against the manager's format settings
        (character set, total length) before hashing.

        Args:
            code_string: The plain text recovery code (e.g., as entered by a user or from generation).

        Returns:
            A hex-encoded SHA-256 hash of the normalized and validated code.

        Raises:
            ValueError: If the code_string is empty, or if the normalized code
                        does not conform to the expected format (length, characters).
        """
        if not code_string:
            raise ValueError("Code string to hash cannot be empty.")

        normalized_code = self._normalize_code(code_string)

        if len(normalized_code) != self.expected_normalized_length:
            raise ValueError(
                f"Normalized code '{normalized_code}' has length {len(normalized_code)}, "
                f"but expected length is {self.expected_normalized_length} "
                f"(based on {self.num_segments} segments of {self.segment_length} chars)."
            )

        for char_idx, char_val in enumerate(normalized_code):
            if char_val not in self.character_set:
                raise ValueError(
                    f"Normalized code '{normalized_code}' contains an invalid character '{char_val}' "
                    f"at position {char_idx}. Character not in allowed set: '{self.character_set}'"
                )

        # Hash the validated, normalized code
        hashed_code = hashlib.sha256(normalized_code.encode('utf-8')).hexdigest()
        return hashed_code


# Example Usage (can be run directly for testing)
if __name__ == "__main__":
    # Default manager
    manager = RecoveryCodesManager()
    print(f"\n--- Default Manager ({manager.num_segments}x{manager.segment_length}) ---")
    default_codes = manager.generate_recovery_codes(count=3)
    print("Generated plain text codes (for user):")
    for code in default_codes:
        print(f"  - {code}")

    print("\nHashed versions (for storage):")
    for code in default_codes:
        try:
            hashed = manager.get_code_hash(code)
            print(f"  - '{code}' -> {hashed}")
        except ValueError as e:
            print(f"  - Error hashing '{code}': {e}")

    # Test verification of a user-typed code
    if default_codes:
        user_typed_code = default_codes[0].lower().replace("-", "  ")  # Simulate user typos
        user_typed_code_mixed_case = default_codes[0][:3].lower() + default_codes[0][3:]
        print(f"\nTesting hashing of user-typed code: '{user_typed_code}' (with spaces, lowercase)")
        try:
            hashed_typed = manager.get_code_hash(
                user_typed_code)  # Normalization should handle spaces if they are just separators
            print(f"  Normalized and hashed: {hashed_typed} (Should match: {manager.get_code_hash(default_codes[0])})")
        except ValueError as e:
            print(f"  Error hashing typed code: {e}")  # This will error if space isn't the defined separator

        print(f"\nTesting hashing of user-typed code: '{user_typed_code_mixed_case}' (mixed case)")
        try:
            hashed_typed_mixed = manager.get_code_hash(user_typed_code_mixed_case)
            print(
                f"  Normalized and hashed: {hashed_typed_mixed} (Should match: {manager.get_code_hash(default_codes[0])})")
        except ValueError as e:
            print(f"  Error hashing typed code: {e}")

    # Test invalid code format
    invalid_code = "ABC-DEF-GHI!"  # Contains invalid character '!' and wrong segment length
    print(f"\nTesting hashing of invalid code: '{invalid_code}'")
    try:
        manager.get_code_hash(invalid_code)
    except ValueError as e:
        print(f"  Correctly caught error: {e}")

    # Shorter codes manager
    shorter_manager = RecoveryCodesManager(num_segments=2, segment_length=4,
                                           character_set="ACEFGHJKLMNPQRUVWXY23456789")
    print(f"\n--- Shorter Manager ({shorter_manager.num_segments}x{shorter_manager.segment_length}) ---")
    shorter_codes = shorter_manager.generate_recovery_codes(count=2)
    for code in shorter_codes:
        print(f"  - {code} -> {shorter_manager.get_code_hash(code)}")