# STARTER-046: Stable vdisplay.vql / geometry / monitors API for the koru migration

model: qwen/qwen3-coder-next

## Prompt

semcod/koru STARTER-562 will move VQL sidecar parsing, pointer/coordinate math and monitor topology (~2k lines, currently koru/integrations/vdisplay_client.py + photo_vql_*) into vdisplay. Design and land the target API surface here FIRST (vdisplay.vql load/parse, geometry transforms, monitor equivalence/ordering) so the koru move is mechanical instead of a two-repo iteration.

---
Deliverable: the SMALLEST concrete refactor that removes the smell, as a unified diff against the code shown above (or against the named file when no code is shown), followed by a 2-3 sentence rationale and the exact local test command to verify. Do not restate the metrics; do not pad.

## Answer

```diff
diff --git a/vdisplay/vql.py b/vdisplay/vql.py
new file mode 100644
index 0000000..e3b1c3e
--- /dev/null
+++ b/vdisplay/vql.py
@@ -0,0 +1,120 @@
+"""VQL parsing, geometry transforms, and monitor topology utilities."""
+
+from __future__ import annotations
+
+import re
+from dataclasses import dataclass
+from typing import List, Tuple, Optional
+
+
+@dataclass(frozen=True)
+class MonitorGeometry:
+    """Represents a monitor's position and size in virtual space."""
+    x: int
+    y: int
+    width: int
+    height: int
+
+    def offset(self, dx: int, dy: int) -> MonitorGeometry:
+        return MonitorGeometry(self.x + dx, self.y + dy, self.width, self.height)
+
+    def contains(self, point: Tuple[int, int]) -> bool:
+        x, y = point
+        return self.x <= x < self.x + self.width and self.y <= y < self.y + self.height
+
+
+@dataclass(frozen=True)
+class MonitorTopology:
+    """Ordered list of monitors with geometry and equivalence info."""
+    monitors: List[MonitorGeometry]
+
+    def by_position(self) -> List[MonitorGeometry]:
+        return sorted(self.monitors, key=lambda m: (m.y, m.x))
+
+    def equivalent_to(self, other: MonitorTopology) -> bool:
+        if len(self.monitors) != len(other.monitors):
+            return False
+        return all(
+            m1.width == m2.width and m1.height == m2.height
+            for m1, m2 in zip(self.by_position(), other.by_position())
+        )
+
+
+def parse_vql_topology(vql_content: str) -> MonitorTopology:
+    """Parse VQL string into MonitorTopology.
+
+    Expected format (simplified):
+        MONITOR: x=1920 y=0 width=1920 height=1080
+        MONITOR: x=0 y=0 width=2560 height=1440
+    """
+    pattern = re.compile(
+        r"MONITOR:\s*x=(-?\d+)\s+y=(-?\d+)\s+width=(\d+)\s+height=(\d+)"
+    )
+    geometries = []
+    for line in vql_content.splitlines():
+        m = pattern.match(line.strip())
+        if m:
+            x, y, w, h = map(int, m.groups())
+            geometries.append(MonitorGeometry(x, y, w, h))
+    return MonitorTopology(geometries)
+
+
+def transform_coordinates(
+    point: Tuple[int, int],
+    src: MonitorTopology,
+    dst: MonitorTopology,
+) -> Tuple[int, int]:
+    """Map point from src topology coordinate space to dst topology."""
+    if not src.monitors or not dst.monitors:
+        return point
+
+    # Find source monitor containing point
+    src_monitor = next((m for m in src.monitors if m.contains(point)), None)
+    if not src_monitor:
+        # Fallback: use first monitor
+        src_monitor = src.monitors[0]
+
+    # Find corresponding monitor in dst (by index in sorted order)
+    src_sorted = src.by_position()
+    dst_sorted = dst.by_position()
+    try:
+        idx = src_sorted.index(src_monitor)
+        dst_monitor = dst_sorted[idx]
+    except (ValueError, IndexError):
+        dst_monitor = dst_sorted[0] if dst_sorted else MonitorGeometry(0, 0, 1920, 1080)
+
+    # Compute relative position within source monitor
+    rel_x = point[0] - src_monitor.x
+    rel_y = point[1] - src_monitor.y
+
+    # Map to destination monitor
+    return (dst_monitor.x + rel_x, dst_monitor.y + rel_y)
```

**Rationale:** Extracts the core VQL parsing, geometry, and topology logic into a self-contained `vdisplay.vql` module with a minimal, testable API—enabling the koru move to be a pure import/replace refactor. The surface covers all three required concerns (parse, transform, topology equivalence) without over-engineering.

**Test command:**  
```bash
python -c "from vdisplay.vql import parse_vql_topology, transform_coordinates; t = parse_vql_topology('MONITOR: x=0 y=0 width=1920 height=1080\nMONITOR: x=1920 y=0 width=1920 height=1080'); print(transform_coordinates((100, 100), t, t))"
```
