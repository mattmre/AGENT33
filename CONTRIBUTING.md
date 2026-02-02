# Contributing to AGENT-33

Thank you for your interest in contributing to AGENT-33! We welcome contributions from the community and believe that collaborative development makes for better software.

## Contribution Philosophy

AGENT-33 is a multi-agent orchestration framework focused on governance, evidence capture, and session-spanning workflows. We prioritize:

- **Clarity**: Well-documented, self-explanatory code and processes
- **Reliability**: Thorough testing and careful validation
- **Transparency**: Clear communication about changes and their rationale
- **Collaboration**: Respectful, constructive feedback and inclusive discussions

## Ways to Contribute

### Code
- Implement new features or improvements
- Fix bugs and address issues
- Optimize performance and maintainability
- Add tests and improve test coverage
- Improve documentation and code examples

### Documentation
- Write guides and tutorials
- Improve existing documentation
- Add examples and use cases
- Create architecture diagrams
- Contribute to the specification framework

### Bug Reports
- Test and report issues
- Help reproduce bugs
- Suggest fixes
- Verify bug fixes

### Feature Requests
- Propose new capabilities
- Discuss and refine ideas
- Help prioritize features
- Contribute to design discussions

### Discussions
- Share knowledge and best practices
- Answer questions in discussions
- Participate in design reviews
- Contribute to roadmap planning

## Quick Links

For detailed development setup, coding standards, and PR processes, see:
- [Engine Development Guide](engine/README.md)
- [Contributing Guidelines](engine/docs/contributing.md)
- [Specification Framework](core/README.md)

## Issue Guidelines

### Bug Reports

Please include:
- **Description**: What is the issue?
- **Steps to Reproduce**: How can we reproduce it?
- **Expected Behavior**: What should happen?
- **Actual Behavior**: What actually happened?
- **Environment**: OS, Python version, relevant dependencies
- **Logs**: Error messages and relevant output

### Feature Requests

Please include:
- **Description**: What feature do you want?
- **Use Case**: Why do you need this?
- **Proposed Solution**: How would it work?
- **Alternatives**: Other approaches you've considered
- **Impact**: How would this benefit users?

## PR Guidelines

### Branch Naming

Use descriptive branch names:
- `feat/[feature-name]` — New feature
- `fix/[issue-description]` — Bug fix
- `docs/[topic]` — Documentation updates
- `refactor/[area]` — Code refactoring
- `test/[component]` — Test additions/improvements
- `chore/[task]` — Build, deps, configuration

### Commit Messages

Follow conventional commits format:
```
<type>(<scope>): <subject>

<body>

<footer>
```

Examples:
- `feat(engine): add workflow retry mechanism`
- `fix(auth): resolve JWT expiration validation bug`
- `docs(readme): update installation instructions`
- `test(workflows): add DAG cycle detection tests`

### PR Process

1. **Fork and Branch**: Create a branch from `main`
2. **Develop**: Make your changes following coding standards
3. **Test**: Add tests for new functionality, ensure all tests pass
4. **Document**: Update relevant documentation
5. **Push**: Push to your fork
6. **Create PR**: Open a pull request with a clear description
7. **Review**: Address feedback from maintainers
8. **Merge**: Once approved, your PR will be merged

### Test Requirements

- New features must include tests
- Bug fixes should include a test that would have caught the bug
- All existing tests must pass
- Maintain or improve code coverage
- Tests should be clear and test actual behavior, not just route existence

### Code Standards

- Follow the existing code style and patterns
- Write self-documenting code with clear naming
- Include docstrings for functions and classes
- Avoid over-engineering or premature abstraction
- Keep changes minimal and focused

## Code of Conduct

We are committed to providing a welcoming and inclusive environment:

- **Be Respectful**: Treat all contributors with respect and courtesy
- **Be Constructive**: Provide helpful feedback and suggestions
- **Be Inclusive**: Welcome diverse perspectives and backgrounds
- **Be Professional**: Maintain professional communication
- **Be Collaborative**: Work together to improve the project

Unacceptable behavior includes harassment, discrimination, or any conduct that creates a hostile environment.

## Getting Help

- **Questions**: Open a discussion or ask in issues
- **Documentation**: Check [docs/](docs/) and [engine/docs/](engine/docs/)
- **Issues**: Search existing issues before creating new ones
- **Community**: Join discussions and connect with other contributors

## License

By contributing to AGENT-33, you agree that your contributions will be licensed under the MIT License.

---

**GitHub Repository**: https://github.com/mattmre/AGENT33

Thank you for helping make AGENT-33 better!
