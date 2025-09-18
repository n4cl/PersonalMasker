# 開発用ユーティリティ Makefile
# 使い方:
#   make backend-test     # backend の pytest を実行
#   make backend-lint     # backend の Ruff チェックを実行
#   make backend-all      # pytest と Ruff を一括実行
#
# 前提: docker compose で backend サービス名は "personal"
#
# コンテナ内判定について:
# - /.dockerenv が存在すれば Docker コンテナ内とみなす（最も簡便）
# - ただし将来のランタイム/イメージ変更で無い可能性もあるため注意
#   代替案:
#     1) /proc/1/cgroup を確認: grep -qE '(docker|containerd)' /proc/1/cgroup
#     2) Dockerfile 側で ENV IN_DOCKER=1 を定義し、それを参照
# - 必要なら上記のいずれかに切替/併用すること
IN_DOCKER := $(shell [ -f /.dockerenv ] && echo 1 || echo 0)

.PHONY: backend-test backend-lint backend-all ensure-personal

ifeq ($(IN_DOCKER),1)
PYTEST_CMD := /opt/venv/bin/pytest -q
RUFF_CMD   := /opt/venv/bin/ruff check backend
ENSURE :=
else
PYTEST_CMD := docker compose exec -T personal bash -lc "/opt/venv/bin/pytest -q"
RUFF_CMD   := docker compose exec -T personal bash -lc "/opt/venv/bin/ruff check backend"
ENSURE := ensure-personal
endif

ensure-personal:
	@docker compose ps --status running --services | grep -qx personal || \
	 (echo "コンテナ 'personal' が起動していません。'docker compose up personal' を実行してください。" && exit 1)

backend-test: $(ENSURE)
	$(PYTEST_CMD)

backend-lint: $(ENSURE)
	$(RUFF_CMD)

backend-all: backend-test backend-lint
