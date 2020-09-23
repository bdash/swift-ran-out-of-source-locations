#!/usr/bin/env python
import errno
import os
import sys

NUMBER_OF_MODULE_MAPS = 5000
NUMBER_OF_TRANSITIVELY_IMPORTED_OBJC_MODULES = 150

def mkdir(path):
  try:
    os.mkdir(path)
  except OSError as e:
    if e.errno != errno.EEXIST:
        raise


def main(_):
  # Change to the script's directory to let us work with relative paths elsewhere
  os.chdir(os.path.dirname(os.path.abspath(__file__)))

  mkdir("module_maps")
  mkdir("headers")

  for i in range(NUMBER_OF_MODULE_MAPS):
    with open("module_maps/module_{}.modulemap".format(i), "w") as f:
      f.write("""\
module "{module}" {{
  export *
  // In real code there would typically be more headers listed here, with longer paths.
  header "../headers/{module}.h"
}}

{comment}
  """.format(module = "module_{}".format(i), comment = 1024 * "// This is a comment that exists solely to increase the size of each module map file\n"))

    with open("headers/module_{}.h".format(i), "w") as f:
      if i < NUMBER_OF_TRANSITIVELY_IMPORTED_OBJC_MODULES:
        f.write("""\
#import "module_{}.h"
""".format(i + 1))

  with open("module_maps/module_map_flags.txt", "w") as f:
    f.write("\n".join(["-Xcc -fmodule-map-file=module_maps/module_{}.modulemap".format(i) for i in range(NUMBER_OF_MODULE_MAPS)]))

if __name__ == "__main__":
  main(sys.argv)
