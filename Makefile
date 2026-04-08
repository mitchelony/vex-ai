.PHONY: test sim clean

test:
	python3 -m unittest discover -s tests

sim:
	python3 -m vexai.sim

clean:
	rm -rf build
