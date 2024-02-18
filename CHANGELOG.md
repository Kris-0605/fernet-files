# Changelog

## v0.1.1

- Add docstrings to all functions (allows you to use Python's built-in `help` function with the module)
- Tests now run on pushes to any branch
- Tests now run when an issue is opened. This is so that if somebody notices that the module does not work with a future version of cryptography, they can make an issue, and tests can quickly determine whether this is indeed what is causing the problem.
- Requirements have been updated so that the module will support any version of cryptography between 36.0.2 and 42.0.2 inclusive.
- Tests are now configured to run on all major versions of cryptography between these two versions.
- Benchmarking information has now been moved from [README.md](/README.md) to [BENCHMARKING.md](/benchmarking/BENCHMARKING.md)
- Benchmarking code and results have been moved from [/tests](/tests) to [/benchmarking](/benchmarking/)
- README documentation has been updated to include a contents page
- README documentation that refers to another part of the documentation now links to that part of the documentation
- The repository for the module now uses CodeQL to scan for vulnerabilities.
- Create [CHANGELOG.md](/CHANGELOG.md)