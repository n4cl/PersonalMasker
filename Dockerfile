FROM public.ecr.aws/docker/library/python:3.12.8-bullseye

RUN apt-get update && apt-get -yq install tzdata less git \
  ca-certificates curl gnupg \
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

# Backend
RUN pip install --upgrade pip && pip install uv
COPY ./pyproject.toml /tmp/
RUN cd /tmp && uv sync

COPY ./ /usr/local/app

CMD ["tail", "-f", "/dev/null"]
