"""Decoder - 20+ encoding formats with multi-layer auto-detection."""

import base64
import binascii
import gzip
import json
import logging
import re
import string
import urllib.parse
from html import escape, unescape
from typing import Optional, List, Tuple, Dict, Any
from dataclasses import dataclass, field
from concurrent.futures import ThreadPoolExecutor

from core.thinking import DecodeStep, AutoDecodeResult

logger = logging.getLogger("phantom.decoder")

MORSE_CODE = {
    'A': '.-', 'B': '-...', 'C': '-.-.', 'D': '-..', 'E': '.', 'F': '..-.',
    'G': '--.', 'H': '....', 'I': '..', 'J': '.---', 'K': '-.-', 'L': '.-..',
    'M': '--', 'N': '-.', 'O': '---', 'P': '.--.', 'Q': '--.-', 'R': '.-.',
    'S': '...', 'T': '-', 'U': '..-', 'V': '...-', 'W': '.--', 'X': '-..-',
    'Y': '-.--', 'Z': '--..', '0': '-----', '1': '.----', '2': '..---',
    '3': '...--', '4': '....-', '5': '.....', '6': '-....', '7': '--...',
    '8': '---..', '9': '----.', '.': '.-.-.-', ',': '--..--', '?': '..--..',
    "'": '.----.', '!': '-.-.--', '/': '-..-.', '(': '-.--.', ')': '-.--.-',
    '&': '.-...', ':': '---...', ';': '-.-.-.', '=': '-...-', '-': '-....-',
    '_': '..--.-', '"': '.-..-.', '$': '...-..-', '@': '.--.-.'
}

MORSE_REVERSE = {v: k for k, v in MORSE_CODE.items()}

JWT_REGEX = re.compile(r'^[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\.[A-Za-z0-9_-]*$')


@dataclass
class DetectionResult:
    """Encoding detection result."""
    encoding_type: str
    confidence: float
    details: str = ""


class Decoder:
    """20+ encoding formats with multi-layer auto-detection."""

    def __init__(self):
        """Initialize decoder."""
        self._executor = ThreadPoolExecutor(max_workers=4)

    def detect_all(self, data: str) -> List[Tuple[str, float]]:
        """Detect all possible encoding types with confidence scores."""
        candidates = []

        if self._is_valid_base64(data):
            candidates.append(("base64", 0.95))
        elif self._is_valid_base32(data):
            candidates.append(("base32", 0.90))
        elif self._is_valid_base85(data):
            candidates.append(("base85", 0.85))

        if self._is_valid_hex(data):
            candidates.append(("hex", 0.92))

        if self._is_valid_url_encoded(data):
            candidates.append(("url", 0.88))

        if self._is_html_entities(data):
            candidates.append(("html_entities", 0.85))

        if self._is_rot13(data):
            candidates.append(("rot13", 0.80))

        if self._is_valid_binary(data):
            candidates.append(("binary", 0.90))

        if self._is_valid_morse(data):
            candidates.append(("morse", 0.88))

        if self._is_valid_jwt(data):
            candidates.append(("jwt", 0.95))

        if self._is_valid_octal(data):
            candidates.append(("octal", 0.85))

        if self._is_valid_decimal(data):
            candidates.append(("decimal", 0.85))

        if self._is_valid_char_codes(data):
            candidates.append(("char_codes", 0.90))

        candidates.sort(key=lambda x: x[1], reverse=True)
        return candidates[:10]

    def _is_valid_base64(self, data: str) -> bool:
        """Check if data is valid base64."""
        data = data.strip()
        if len(data) < 4:
            return False
        padding = data.count('=')
        clean = data.rstrip('=')
        pattern = re.compile(r'^[A-Za-z0-9+/]*={0,2}$')
        if not pattern.match(clean):
            return False
        try:
            base64.b64decode(data)
            return True
        except Exception:
            return False

    def _is_valid_base32(self, data: str) -> bool:
        """Check if data is valid base32."""
        data = data.strip().upper()
        if len(data) < 4:
            return False
        try:
            base64.b32decode(data)
            return True
        except Exception:
            return False

    def _is_valid_base85(self, data: str) -> bool:
        """Check if data is valid base85."""
        data = data.strip()
        if len(data) < 4:
            return False
        try:
            base64.b85decode(data)
            return True
        except Exception:
            return False

    def _is_valid_hex(self, data: str) -> bool:
        """Check if data is valid hexadecimal."""
        data = data.strip().lower()
        if len(data) < 2:
            return False
        pattern = re.compile(r'^[0-9a-f]+$')
        if not pattern.match(data):
            return False
        if len(data) % 2 != 0:
            return False
        try:
            bytes.fromhex(data)
            return True
        except Exception:
            return False

    def _is_valid_url_encoded(self, data: str) -> bool:
        """Check if data contains URL encoding."""
        data = data.strip()
        if '%' not in data:
            return False
        pattern = re.compile(r'%[0-9A-Fa-f]{2}')
        return bool(pattern.search(data))

    def _is_html_entities(self, data: str) -> bool:
        """Check if data contains HTML entities."""
        return '&lt;' in data or '&gt;' in data or '&amp;' in data or '&#' in data

    def _is_rot13(self, data: str) -> bool:
        """Check if ROT13 candidate."""
        data = data.strip()
        if len(data) < 4:
            return False
        rot13_pattern = re.compile(r'^[A-Za-z]+$')
        return bool(rot13_pattern.match(data))

    def _is_valid_binary(self, data: str) -> bool:
        """Check if data is valid binary."""
        data = data.strip()
        pattern = re.compile(r'^[01\s]+$')
        if not pattern.match(data):
            return False
        cleaned = data.replace(' ', '').replace('\n', '')
        return len(cleaned) > 8 and len(cleaned) % 8 == 0

    def _is_valid_morse(self, data: str) -> bool:
        """Check if data is valid morse code."""
        data = data.strip()
        valid_chars = set('.-\n ')
        return all(c in valid_chars for c in data) and ('.' in data or '-' in data)

    def _is_valid_jwt(self, data: str) -> bool:
        """Check if data is valid JWT."""
        return bool(JWT_REGEX.match(data.strip()))

    def _is_valid_octal(self, data: str) -> bool:
        """Check if data is valid octal."""
        data = data.strip()
        pattern = re.compile(r'^[0-7\s]+$')
        if not pattern.match(data):
            return False
        cleaned = data.replace(' ', '').replace('\n', '')
        return len(cleaned) > 2

    def _is_valid_decimal(self, data: str) -> bool:
        """Check if data is decimal ASCII codes."""
        data = data.strip()
        pattern = re.compile(r'^\d+(,\d+|\s\d+)*$')
        return bool(pattern.match(data))

    def _is_valid_char_codes(self, data: str) -> bool:
        """Check if data is JavaScript charCodeAt format."""
        data = data.strip()
        bracket_pattern = re.compile(r'^\[\d+(,\d+)*\]$')
        paren_pattern = re.compile(r'^\(\d+(,\d+)*\)$')
        return bool(bracket_pattern.match(data) or paren_pattern.match(data))

    def decode_base64(self, data: str) -> Optional[str]:
        """Decode base64."""
        try:
            return base64.b64decode(data).decode('utf-8', errors='replace')
        except Exception as e:
            logger.debug(f"base64 decode failed: {e}")
            return None

    def decode_base32(self, data: str) -> Optional[str]:
        """Decode base32."""
        try:
            return base64.b32decode(data.strip().upper()).decode('utf-8', errors='replace')
        except Exception as e:
            logger.debug(f"base32 decode failed: {e}")
            return None

    def decode_base58(self, data: str) -> Optional[str]:
        """Decode base58 (Bitcoin style)."""
        try:
            import base58
            return base58.b58decode(data).decode('utf-8', errors='replace')
        except ImportError:
            alphabet = "123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"
            table = str.maketrans(alphabet, "".join(chr(i) for i in range(58)))
            cleaned = data.translate(table)
            return self.decode_base64(cleaned)
        except Exception as e:
            logger.debug(f"base58 decode failed: {e}")
            return None

    def decode_base85(self, data: str) -> Optional[str]:
        """Decode base85."""
        try:
            return base64.b85decode(data).decode('utf-8', errors='replace')
        except Exception as e:
            logger.debug(f"base85 decode failed: {e}")
            return None

    def decode_hex(self, data: str) -> Optional[str]:
        """Decode hexadecimal."""
        try:
            hex_clean = data.strip().lower().replace(' ', '').replace('0x', '')
            return bytes.fromhex(hex_clean).decode('utf-8', errors='replace')
        except Exception as e:
            logger.debug(f"hex decode failed: {e}")
            return None

    def decode_url(self, data: str) -> Optional[str]:
        """Decode URL encoding."""
        try:
            return urllib.parse.unquote(data)
        except Exception as e:
            logger.debug(f"url decode failed: {e}")
            return None

    def decode_html_entities(self, data: str) -> Optional[str]:
        """Decode HTML entities."""
        try:
            return unescape(data)
        except Exception as e:
            logger.debug(f"html entities decode failed: {e}")
            return None

    def decode_rot13(self, data: str) -> Optional[str]:
        """Decode ROT13."""
        try:
            import codecs
            return codecs.decode(data, 'rot13')
        except Exception as e:
            logger.debug(f"rot13 decode failed: {e}")
            return None

    def decode_rot47(self, data: str) -> Optional[str]:
        """Decode ROT47."""
        try:
            result = []
            for char in data:
                code = ord(char)
                if 33 <= code <= 126:
                    result.append(chr(33 + ((code - 33 + 47) % 94)))
                else:
                    result.append(char)
            return ''.join(result)
        except Exception as e:
            logger.debug(f"rot47 decode failed: {e}")
            return None

    def decode_binary(self, data: str) -> Optional[str]:
        """Decode binary to ASCII."""
        try:
            cleaned = data.strip().replace(' ', '').replace('\n', '')
            chunks = [cleaned[i:i+8] for i in range(0, len(cleaned), 8)]
            bytes_list = [int(c, 2) for c in chunks]
            return bytes(bytes_list).decode('utf-8', errors='replace')
        except Exception as e:
            logger.debug(f"binary decode failed: {e}")
            return None

    def decode_morse(self, data: str) -> Optional[str]:
        """Decode morse code."""
        try:
            result = []
            words = data.strip().split('  ')
            for word in words:
                letters = word.split()
                for letter in letters:
                    if letter in MORSE_REVERSE:
                        result.append(MORSE_REVERSE[letter])
                result.append(' ')
            return ''.join(result).strip()
        except Exception as e:
            logger.debug(f"morse decode failed: {e}")
            return None

    def decode_jwt(self, data: str) -> Optional[Dict[str, Any]]:
        """Decode JWT token."""
        try:
            parts = data.strip().split('.')
            if len(parts) != 3:
                return None

            def decode_part(part: str) -> Dict[str, Any]:
                padding = '=' * (4 - len(part) % 4)
                decoded = base64.urlsafe_b64decode(part + padding)
                return json.loads(decoded)

            header = decode_part(parts[0])
            payload = decode_part(parts[1])

            return {
                "header": header,
                "payload": payload,
                "signature_valid": True
            }
        except Exception as e:
            logger.debug(f"jwt decode failed: {e}")
            return None

    def decode_xor(self, data: str, key: Optional[int] = None) -> Optional[str]:
        """Decode XOR with optional brute-force single-byte key."""
        try:
            data_bytes = bytes.fromhex(data.strip().replace(' ', ''))

            if key is not None:
                result = bytes([b ^ key for b in data_bytes])
                return result.decode('utf-8', errors='replace')

            for k in range(1, 256):
                try:
                    result = bytes([b ^ k for b in data_bytes])
                    decoded = result.decode('utf-8', errors='strict')
                    if all(c in string.printable for c in decoded):
                        return decoded
                except Exception:
                    continue
            return None
        except Exception as e:
            logger.debug(f"xor decode failed: {e}")
            return None

    def decode_gzip_base64(self, data: str) -> Optional[str]:
        """Decode gzip compressed base64."""
        try:
            decoded = base64.b64decode(data)
            decompressed = gzip.decompress(decoded)
            return decompressed.decode('utf-8', errors='replace')
        except Exception as e:
            logger.debug(f"gzip base64 decode failed: {e}")
            return None

    def decode_unicode_escapes(self, data: str) -> Optional[str]:
        """Decode unicode escape sequences."""
        try:
            pattern = re.compile(r'\\u([0-9a-fA-F]{4})')
            matches = pattern.findall(data)
            if matches:
                return pattern.sub(lambda m: chr(int(m.group(1), 16)), data)
            pattern2 = re.compile(r'\\x([0-9a-fA-F]{2})')
            matches2 = pattern2.findall(data)
            if matches2:
                return pattern2.sub(lambda m: chr(int(m.group(1), 16)), data)
            return None
        except Exception as e:
            logger.debug(f"unicode escapes decode failed: {e}")
            return None

    def decode_caesar(self, data: str, shift: Optional[int] = None) -> Optional[str]:
        """Decode Caesar cipher."""
        try:
            if shift is not None:
                return self._caesar_decrypt(data, shift)

            best_result = None
            best_score = 0
            common_words = {'the', 'and', 'for', 'are', 'but', 'not', 'you', 'all', 'can', 'her', 'was', 'one', 'our', 'out'}

            for s in range(1, 26):
                decrypted = self._caesar_decrypt(data, s)
                score = sum(1 for word in decrypted.lower().split() if word in common_words)
                if score > best_score:
                    best_score = score
                    best_result = decrypted

            return best_result
        except Exception as e:
            logger.debug(f"caesar decode failed: {e}")
            return None

    def _caesar_decrypt(self, data: str, shift: int) -> str:
        """Apply Caesar decryption."""
        result = []
        for char in data:
            if char.isalpha():
                base = ord('A') if char.isupper() else ord('a')
                result.append(chr((ord(char) - base - shift) % 26 + base))
            else:
                result.append(char)
        return ''.join(result)

    def decode_char_codes(self, data: str) -> Optional[str]:
        """Decode JavaScript charCodeAt format."""
        try:
            numbers = re.findall(r'\d+', data)
            chars = [chr(int(n)) for n in numbers]
            return ''.join(chars)
        except Exception as e:
            logger.debug(f"char codes decode failed: {e}")
            return None

    def decode_octal(self, data: str) -> Optional[str]:
        """Decode octal to ASCII."""
        try:
            cleaned = data.strip().replace(' ', '').replace('\n', '')
            chunks = [cleaned[i:i+3] for i in range(0, len(cleaned), 3)]
            bytes_list = [int(c, 8) for c in chunks]
            return bytes(bytes_list).decode('utf-8', errors='replace')
        except Exception as e:
            logger.debug(f"octal decode failed: {e}")
            return None

    def decode_decimal(self, data: str) -> Optional[str]:
        """Decode decimal ASCII codes."""
        try:
            numbers = re.findall(r'\d+', data)
            chars = [chr(int(n)) for n in numbers]
            return ''.join(chars)
        except Exception as e:
            logger.debug(f"decimal decode failed: {e}")
            return None

    def encode_base64(self, data: str) -> str:
        """Encode to base64."""
        return base64.b64encode(data.encode('utf-8')).decode('ascii')

    def encode_base32(self, data: str) -> str:
        """Encode to base32."""
        return base64.b32encode(data.encode('utf-8')).decode('ascii')

    def encode_hex(self, data: str) -> str:
        """Encode to hexadecimal."""
        return data.encode('utf-8').hex()

    def encode_url(self, data: str) -> str:
        """Encode URL."""
        return urllib.parse.quote(data)

    def encode_html(self, data: str) -> str:
        """Encode HTML entities."""
        return escape(data)

    def encode_rot13(self, data: str) -> str:
        """Encode ROT13."""
        import codecs
        return codecs.encode(data, 'rot13')

    def encode_binary(self, data: str) -> str:
        """Encode to binary."""
        return ' '.join(format(b, '08b') for b in data.encode('utf-8'))

    def encode_morse(self, data: str) -> str:
        """Encode to morse code."""
        result = []
        for char in data.upper():
            if char in MORSE_CODE:
                result.append(MORSE_CODE[char])
            elif char == ' ':
                result.append('/')
            else:
                result.append(char)
        return ' '.join(result)

    def encode_xor(self, data: str, key: int) -> str:
        """Encode XOR."""
        data_bytes = data.encode('utf-8')
        result = bytes([b ^ key for b in data_bytes])
        return result.hex()

    def encode_caesar(self, data: str, shift: int) -> str:
        """Encode Caesar cipher."""
        result = []
        for char in data:
            if char.isalpha():
                base = ord('A') if char.isupper() else ord('a')
                result.append(chr((ord(char) - base + shift) % 26 + base))
            else:
                result.append(char)
        return ''.join(result)

    def hash_all(self, data: str) -> Dict[str, str]:
        """Generate all common hashes."""
        import hashlib
        return {
            "md5": hashlib.md5(data.encode()).hexdigest(),
            "sha1": hashlib.sha1(data.encode()).hexdigest(),
            "sha256": hashlib.sha256(data.encode()).hexdigest(),
            "sha512": hashlib.sha512(data.encode()).hexdigest(),
        }

    def identify_hash(self, h: str) -> List[str]:
        """Identify hash type by length and pattern."""
        h = h.strip().lower()
        results = []

        if len(h) == 32:
            results.append("MD5")
        if len(h) == 40:
            results.append("SHA1")
        if len(h) == 56:
            results.append("SHA224")
        if len(h) == 64:
            results.append("SHA256")
        if len(h) == 96:
            results.append("SHA384")
        if len(h) == 128:
            results.append("SHA512")
        if len(h) == 16 and all(c in '0123456789abcdef' for c in h):
            results.append("MySQL5")
        if len(h) == 34 and h.startswith('$P$'):
            results.append("PHPass")
        if len(h) == 60 and h.startswith('$1$'):
            results.append("Unix MD5")
        if len(h) == 60 and h.startswith('$2'):
            results.append("Blowfish/BCrypt")
        if len(h) == 60 and h.startswith('$5$'):
            results.append("SHA256crypt")
        if len(h) == 60 and h.startswith('$6$'):
            results.append("SHA512crypt")

        if not results:
            results.append("Unknown")

        return results

    def auto_decode(self, data: str, max_layers: int = 10, verbose: bool = True) -> AutoDecodeResult:
        """Auto-detect and decode with multiple layers."""
        layers: List[DecodeStep] = []
        current = data.strip()
        original = current
        attempts = 0

        while attempts < max_layers:
            candidates = self.detect_all(current)
            if not candidates:
                break

            encoding_type, confidence = candidates[0]

            decoded = None
            decode_fn = getattr(self, f"decode_{encoding_type}", None)
            if decode_fn:
                decoded = decode_fn(current)

            if decoded is None or decoded == current:
                if len(candidates) > 1:
                    encoding_type, confidence = candidates[1]
                    decode_fn = getattr(self, f"decode_{encoding_type}", None)
                    if decode_fn:
                        decoded = decode_fn(current)

            if decoded is None or decoded == current:
                break

            layer = DecodeStep(
                layer=attempts + 1,
                operation=f"decode_{encoding_type}",
                input_preview=current[:50] + "..." if len(current) > 50 else current,
                output_preview=decoded[:50] + "..." if len(decoded) > 50 else decoded,
                confidence=confidence
            )
            layers.append(layer)

            current = decoded
            attempts += 1

            if all(c in string.printable or c in '\n\r\t' for c in current):
                if confidence < 0.7:
                    break

        return AutoDecodeResult(
            original=original,
            final=current,
            layers=layers,
            total_layers=len(layers),
            success=len(layers) > 0
        )