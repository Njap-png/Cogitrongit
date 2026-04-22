"""Decoder Agent - Multi-layer decode analysis."""

import logging
from typing import Optional, Dict, Any, List

from agents.base_agent import BaseAgent
from tools.decoder import Decoder

logger = logging.getLogger("phantom.decoderagent")


class DecoderAgent(BaseAgent):
    """Agent for decode/encode operations."""

    def __init__(self, *args, **kwargs):
        """Initialize decoder agent."""
        super().__init__(*args, **kwargs)
        self.decoder = Decoder()

    async def run(
        self,
        task: str,
        context: Optional[Dict[str, Any]] = None
    ) -> str:
        """Run decode task."""
        parts = task.split(None, 1)
        command = parts[0].lower()
        data = parts[1] if len(parts) > 1 else ""

        if not data:
            return "No data provided."

        if command == "decode":
            return await self.auto_decode(data)

        if command == "detect":
            return self.detect(data)

        if command == "encode":
            if len(parts) < 3:
                return "Usage: encode <format> <data>"
            return self.encode(parts[2], parts[1])

        if command == "hash":
            return self.hash(data)

        return await self.auto_decode(data)

    async def auto_decode(
        self,
        data: str,
        max_layers: int = 10,
        verbose: bool = True
    ) -> str:
        """Auto-detect and decode."""
        result = self.decoder.auto_decode(data, max_layers, verbose)

        if not result.success:
            return "Could not decode the data."

        output = f"## Decode Result\n\n"
        output += f"**Original ({result.total_layers} layers):**\n"
        output += f"```\n{result.original[:200]}\n```\n\n"
        output += f"**Final:**\n```\n{result.final}\n```\n\n"

        if verbose and result.layers:
            output += "**Layers:**\n"
            for layer in result.layers:
                output += f"- {layer.layer}. `{layer.operation}` ({layer.confidence:.0%})\n"
                output += f"  Input: `{layer.input_preview[:50]}...`\n"
                output += f"  Output: `{layer.output_preview[:50]}...`\n"

        return output

    def detect(self, data: str) -> str:
        """Detect encoding type."""
        candidates = self.decoder.detect_all(data)

        if not candidates:
            return "Could not identify encoding type."

        output = "## Encoding Detection\n\n"
        output += "| Format | Confidence |\n"
        output += "|-------|------------|\n"

        for encoding_type, confidence in candidates[:10]:
            output += f"| {encoding_type} | {confidence:.0%} |\n"

        return output

    def encode(self, format_type: str, data: str) -> str:
        """Encode data."""
        method_name = f"encode_{format_type}"
        method = getattr(self.decoder, method_name, None)

        if not method:
            return f"Unknown format: {format_type}"

        try:
            result = method(data)
            return f"**{format_type.upper()}:**\n```\n{result}\n```"
        except Exception as e:
            return f"Encoding failed: {e}"

    def hash(self, data: str) -> str:
        """Generate all hashes."""
        hashes = self.decoder.hash_all(data)

        output = "## Hashes\n\n"
        for hash_type, hash_value in hashes.items():
            output += f"**{hash_type.upper()}:** `{hash_value}`\n"

        return output

    def get_capabilities(self) -> List[str]:
        """Get agent capabilities."""
        return [
            "auto_decode",
            "encoding_detect",
            "encode",
            "hash",
        ]