FROM debian:bookworm-slim


RUN apt update && apt install -y curl unzip procps
RUN curl -o- https://fnm.vercel.app/install | bash
RUN echo 'eval "$(fnm env --use-on-cd --shell bash)"' >> ~/.profile
RUN bash -c "source ~/.profile; fnm install 22.14.0; fnm install 23.11.0"
CMD [ "bash" ]