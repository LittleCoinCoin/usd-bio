import hashlib
import io
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt


def render(metadata=None):
    fig, ax = plt.subplots(figsize=(4, 3), dpi=100)
    ax.plot([0, 1, 2, 3], [0.1, 0.4, 0.35, 0.8])
    buf = io.BytesIO()
    fig.savefig(buf, format="png", metadata=metadata)
    plt.close(fig)
    return buf.getvalue()


a = render()
b = render()
print("matplotlib", matplotlib.__version__, "python", sys.version.split()[0])
print("same-process default: identical =", a == b, hashlib.sha256(a).hexdigest()[:16])
idx = a.find(b"Software")
print("Software chunk:", a[idx:idx + 60] if idx >= 0 else None)
c = render(metadata={"Software": None})
print("Software stripped present =", b"Software" in c, hashlib.sha256(c).hexdigest()[:16])
