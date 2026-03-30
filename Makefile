.PHONY: test sim clean

test:
	python3 -m unittest tests.test_strategy

sim:
	python3 -m vexai.sim

clean:
	rm -rf build
