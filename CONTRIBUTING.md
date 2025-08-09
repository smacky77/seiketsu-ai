# Contributing to Seiketsu AI

First off, thank you for considering contributing to Seiketsu AI! It's people like you that make Seiketsu AI such a great tool.

## 📋 Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [How Can I Contribute?](#how-can-i-contribute)
- [Development Process](#development-process)
- [Style Guidelines](#style-guidelines)
- [Commit Messages](#commit-messages)
- [Pull Request Process](#pull-request-process)
- [Community](#community)

## Code of Conduct

This project and everyone participating in it is governed by our [Code of Conduct](CODE_OF_CONDUCT.md). By participating, you are expected to uphold this code.

## Getting Started

1. **Fork the repository** on GitHub
2. **Clone your fork** locally
3. **Set up the development environment** following our [README](README.md#quick-start)
4. **Create a branch** for your changes

## How Can I Contribute?

### 🐛 Reporting Bugs

Before creating bug reports, please check existing issues. When creating a bug report, include:

- **Clear title and description**
- **Steps to reproduce**
- **Expected behavior**
- **Actual behavior**
- **Screenshots** (if applicable)
- **Environment details**

### ✨ Suggesting Enhancements

Enhancement suggestions are tracked as GitHub issues. Include:

- **Clear title and description**
- **Use case and benefits**
- **Possible implementation**
- **Alternative solutions considered**

### 📝 Your First Code Contribution

Unsure where to begin? Look for issues labeled:

- `good first issue` - Simple fixes for beginners
- `help wanted` - More involved issues
- `documentation` - Documentation improvements

## Development Process

### 1. 🌿 Branch Naming

Use descriptive branch names:
- `feature/voice-emotion-detection`
- `fix/api-timeout-issue`
- `docs/update-deployment-guide`
- `chore/update-dependencies`

### 2. 🧪 Testing

Ensure all tests pass:
```bash
npm run test
npm run lint
npm run typecheck
```

Add tests for new features:
- Unit tests for functions
- Integration tests for APIs
- E2E tests for user flows

### 3. 📚 Documentation

Update documentation for:
- New features
- API changes
- Configuration changes
- Breaking changes

## Style Guidelines

### TypeScript/JavaScript

- Use TypeScript for all new code
- Follow ESLint configuration
- Use functional components in React
- Prefer composition over inheritance

```typescript
// Good
export const VoiceAgent: FC<VoiceAgentProps> = ({ config }) => {
  const [state, setState] = useState<AgentState>('idle');
  // ...
};

// Avoid
class VoiceAgent extends Component {
  // ...
}
```

### Python

- Follow PEP 8
- Use type hints
- Write docstrings for functions
- Use async/await for I/O operations

```python
# Good
async def process_voice_input(
    audio_data: bytes,
    config: VoiceConfig
) -> ProcessedAudio:
    """Process raw audio input with voice configuration."""
    # ...
```

### CSS/Styling

- Use Tailwind CSS utilities
- Create custom components for repeated patterns
- Follow mobile-first approach

## Commit Messages

Follow [Conventional Commits](https://www.conventionalcommits.org/):

```
<type>(<scope>): <subject>

<body>

<footer>
```

### Types
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation
- `style`: Formatting
- `refactor`: Code restructuring
- `perf`: Performance improvement
- `test`: Testing
- `chore`: Maintenance

### Examples
```
feat(voice): add emotion detection to voice processing

Implement real-time emotion detection using sentiment analysis
on transcribed text and voice tone analysis.

Closes #123
```

## Pull Request Process

1. **Update documentation** including README if needed
2. **Add/update tests** for your changes
3. **Ensure CI passes** all checks
4. **Request review** from maintainers
5. **Address feedback** promptly
6. **Squash commits** if requested

### PR Template

```markdown
## Description
Brief description of changes

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation update

## Testing
- [ ] Unit tests pass
- [ ] Integration tests pass
- [ ] Manual testing completed

## Checklist
- [ ] Code follows style guidelines
- [ ] Self-review completed
- [ ] Documentation updated
- [ ] No new warnings
```

## Community

### 💬 Communication Channels

- **GitHub Issues**: Bug reports and feature requests
- **GitHub Discussions**: General discussions
- **Discord**: Real-time chat (coming soon)
- **Twitter**: [@seiketsuai](https://twitter.com/seiketsuai)

### 🎯 Project Roadmap

Check our [Project Board](https://github.com/smacky77/seiketsu-ai/projects) for:
- Current priorities
- Upcoming features
- Known issues
- Release planning

### 👥 Core Team

- **@smacky77** - Project Lead
- **@ai-team** - AI Development
- **@platform-team** - Platform Development

## Recognition

Contributors are recognized in:
- [README Contributors section](README.md#contributors)
- Release notes
- Project documentation

## Questions?

Feel free to:
- Open an issue
- Start a discussion
- Contact maintainers

Thank you for contributing to Seiketsu AI! 🎉