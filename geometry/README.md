# geometry

Plots a geometry for a given .hdr and -mod.par files.

# Requirements:

Python3.10 (not tested in previous versions)

```
pip install -r requirements.txt
```

# Running

Use --help to get instructions:
```sh
python geometry.py --help
```

Example:
```
python geometry.py --par ../../tests/jesse-mod.par --hdr ../../tests/jesse.hdr --vel ../../tests/jesse.bin --slice=100
```

output will be in .png files inside `output` dir. 
