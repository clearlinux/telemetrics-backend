tag-production:
	@TODAY=`date "+%F-%H%M%S"`; \
	git rev-parse production-$$TODAY &> /dev/null; \
	if [ "$$?" -eq 0 ]; then \
		echo "Error: production tag for $$TODAY already exists."; \
		exit 1; \
	fi; \
	git tag -a -m "snapshot deployed on $$TODAY" production-$$TODAY; \
	printf "\nTagged production-$$TODAY!\n\n"
