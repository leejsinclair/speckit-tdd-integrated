#!/bin/sh
# A framework-neutral stand-in for a project's test command.
# Usage: fake_test.sh <selector>
case "$1" in
  pass)
    echo "ok"
    exit 0
    ;;
  assert)
    echo "AssertionError: expected 0 got None"
    exit 1
    ;;
  import)
    echo "ModuleNotFoundError: no module named cart"
    exit 1
    ;;
  slow)
    sleep 5
    echo "ok"
    exit 0
    ;;
  long)
    i=1
    while [ "$i" -le 60 ]; do
      echo "line $i"
      i=$((i + 1))
    done
    exit 1
    ;;
  *)
    echo "fake_test.sh: unknown selector: $1" >&2
    exit 3
    ;;
esac
