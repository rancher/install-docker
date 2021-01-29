TARGETS := $(shell ls scripts)

$(TARGETS):
	@sh -c "'$(CURDIR)/scripts/$@'"

.DEFAULT_GOAL := generate

.PHONY: $(TARGETS)