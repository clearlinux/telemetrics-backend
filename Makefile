VERSION = 1.0.0

release:
	@git rev-parse v$(VERSION) &> /dev/null; \
	if [ "$$?" -eq 0 ]; then \
		echo "Error: Release $(VERSION) already exists."; \
		echo "Bump version in the Makefile before releasing."; \
		exit 1; \
	fi; \
	if $$(git status --porcelain | grep -q "M Makefile"); then \
		echo "Error: Refusing to release with uncommitted changes to Makefile."; \
		echo "Commit or discard these changes before releasing."; \
		exit 1; \
	fi; \
	git tag -a -m "Release $(VERSION)" v$(VERSION); \
	printf "\nNew release $(VERSION) tagged!\n\n"

run-tests:
	PYTHONPATH=/$(shell pwd)/collector python3 collector/collector/tests/handler.py
	PYTHONPATH=/$(shell pwd)/collector python3 collector/collector/tests/rest_api.py

tag-production:
	@TODAY=`date "+%F-%H%M%S"`; \
	git rev-parse production-$$TODAY &> /dev/null; \
	if [ "$$?" -eq 0 ]; then \
		echo "Error: production tag for $$TODAY already exists."; \
		exit 1; \
	fi; \
	git tag -a -m "snapshot deployed on $$TODAY" production-$$TODAY; \
	printf "\nTagged production-$$TODAY!\n\n"
