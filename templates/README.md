# Filtergraph templates

Each `.txt` file is an ffmpeg filtergraph with `{{placeholder}}` values filled in
from a song's `sounds.md`. Templates are written over several indented lines for
readability.

`fftechno/synth.py` preprocesses a template before substitution:

- blank lines are ignored;
- lines whose first non-space character is `#` are comments and are ignored;
- the remaining lines are joined with a single space.

This is the same idea as Perl's `/x` extended regex mode: line breaks and
indentation do not change the graph. A line must not split a token in half, so break
at safe boundaries such as `;`, `,` or before a `+` operator.

The generated graphs are written to `filters/<song>/<name>.txt` and are gitignored;
the templates are the source of truth.