# [Zvorky.github.io](https://zvorky.github.io/)
Sharing open knowledge for everyone.  
[@zvorky](https://github.com/zvorky)

This GitHub Pages repository is dedicated to sharing open knowledge about technology, coding, hardware, security, and more.  
Basically, this is a place where I share my journey in Computer Engineering and related fields. 

- [English](docs/en/README.md)
- [Português](docs/pt/README.md)

## Architecture
This repository is organized in two main branches:
- `main` - where I write and maintain all the articles in Markdown format, besides the python code that generates the static website.
- `gh-pages` - where the generated static website is hosted. This branch is automatically updated whenever there are changes in the `main` branch.

### Architecture Decision Record (ADR)
Further architectural details are specified in the [dev/ARCHITECTURE.md](dev/ARCHITECTURE.md) file.
> The ADR file is generated and maintained using my own python module CLI [`adrtools`](https://github.com/zvorky/adrtools)

## License

### **Source Code** - [MIT License](/LICENSE)
**Scope:** All source code in this repository, including the static website generator.  

> This means you are free to use, copy, modify, redistribute, sell, and even close-source the code.

### **Intellectual Property** - [CC BY 4.0](/docs/en/LICENSE.md)
**Scope:** All the media and written content under [docs/](docs/) directory and the `gh-pages` branch.

> This means you are free to share and adapt the content, even for commercial purposes, as long as you give appropriate credits and indicate if changes were made.