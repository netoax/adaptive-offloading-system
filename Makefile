USR_DIR := /usr/local

SCALA_VERSION := 2.11
APACHE_FLINK_VERSION := 1.12.2
APACHE_FLINK_URL := https://downloads.apache.org/flink/flink-$(APACHE_FLINK_VERSION)/flink-$(APACHE_FLINK_VERSION)-bin-scala_$(SCALA_VERSION).tgz

.PHONY: deps-flink
deps-flink:
	@echo "installing apache flink"
	@curl -s -L $(APACHE_FLINK_URL) | tar xz -C /tmp \
	&& mv flink-$(APACHE_FLINK_VERSION)-bin-scala_$(SCALA_VERSION) $(USR_DIR)/apache-flink
