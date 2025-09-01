FROM public.ecr.aws/docker/library/python:3.12-bookworm

RUN apt-get update && apt-get install -y \
    tzdata \
    less \
    git \
    ca-certificates \
    curl \
    gnupg \
    build-essential \
    gcc \
    g++ \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*


# TimeZone
RUN echo "Asia/Tokyo" > /etc/timezone \
  && rm /etc/localtime \
  && ln -s /usr/share/zoneinfo/Asia/Tokyo /etc/localtime \
  && dpkg-reconfigure -f noninteractive tzdata

# ginza (for sudachipy)
ENV PATH=$PATH:/root/.cargo/bin
RUN curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs > /tmp/rust.sh
RUN sh /tmp/rust.sh -y

WORKDIR /usr/local/app

# Backend
RUN pip install --upgrade pip && pip install uv

# Set environment variables to help with compilation
ENV CFLAGS="-Wno-error"
ENV CXXFLAGS="-Wno-error"

# Keep the project virtualenv outside the bind mount so it's not masked by the volume
ENV UV_PROJECT_ENVIRONMENT=/opt/venv

# Only copy dependency files first to leverage Docker layer caching
COPY ./pyproject.toml ./
COPY ./uv.lock ./

# Install Python dependencies into /opt/venv (respects uv.lock if present)
RUN uv sync --frozen

# Ensure the venv is on PATH for runtime
ENV PATH="/opt/venv/bin:$PATH"

# Copy the rest of the app source
COPY ./ /usr/local/app

CMD ["tail", "-f", "/dev/null"]
