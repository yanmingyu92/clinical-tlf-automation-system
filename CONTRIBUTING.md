# Contributing to Clinical TLF Automation System

Thank you for your interest in contributing to the Clinical TLF Automation System! This document provides guidelines for contributing to the project.

## 🚀 Getting Started

### Prerequisites

- Python 3.8+
- R 4.0+ (optional for development)
- Git
- Basic understanding of clinical trial data and TLF generation

### Development Setup

1. **Fork the repository**
   ```bash
   git clone https://github.com/your-username/r_tlf_system.git
   cd r_tlf_system
   ```

2. **Create a virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure for development**
   ```bash
   cp config/config.example.json config/config.json
   # Add your API keys for testing
   ```

## 📋 How to Contribute

### Reporting Issues

- Use the GitHub issue tracker
- Provide clear description of the problem
- Include steps to reproduce
- Add relevant logs or error messages
- Specify your environment (OS, Python version, etc.)

### Suggesting Features

- Open an issue with the "enhancement" label
- Describe the feature and its benefits
- Provide use cases and examples
- Consider implementation complexity

### Code Contributions

1. **Create a feature branch**
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Make your changes**
   - Follow the coding standards below
   - Add tests if applicable
   - Update documentation

3. **Test your changes**
   ```bash
   python app/real_production_launcher.py
   # Test the UI at http://localhost:8008
   ```

4. **Commit your changes**
   ```bash
   git add .
   git commit -m "Add: brief description of changes"
   ```

5. **Push and create PR**
   ```bash
   git push origin feature/your-feature-name
   # Create pull request on GitHub
   ```

## 🎯 Areas for Contribution

### High Priority
- Additional LLM provider integrations
- Enhanced error handling and debugging
- Performance optimizations
- Documentation improvements

### Medium Priority
- New template types and formats
- Advanced statistical functions
- UI/UX enhancements
- Test coverage expansion

### Low Priority
- Code refactoring
- Additional utility scripts
- Example datasets
- Internationalization

## 📝 Coding Standards

### Python Code Style
- Follow PEP 8 guidelines
- Use meaningful variable and function names
- Add docstrings for functions and classes
- Keep functions focused and small
- Use type hints where appropriate

### JavaScript/HTML/CSS
- Use consistent indentation (2 spaces)
- Follow modern ES6+ standards
- Add comments for complex logic
- Maintain responsive design principles

### R Code
- Follow tidyverse style guide
- Use meaningful variable names
- Add comments for complex operations
- Ensure reproducibility

## 🧪 Testing Guidelines

### Manual Testing
- Test the 4-step workflow end-to-end
- Verify UI responsiveness
- Check error handling
- Test with different LLM providers

### Code Testing
- Add unit tests for new functions
- Test edge cases and error conditions
- Ensure backward compatibility
- Test with sample datasets

## 📚 Documentation

### Code Documentation
- Add docstrings to all functions
- Include parameter descriptions
- Provide usage examples
- Document return values

### User Documentation
- Update README.md for new features
- Add examples and use cases
- Include configuration instructions
- Provide troubleshooting guides

## 🔄 Pull Request Process

### Before Submitting
- [ ] Code follows style guidelines
- [ ] Tests pass (if applicable)
- [ ] Documentation is updated
- [ ] No merge conflicts
- [ ] Commit messages are clear

### PR Description
- Describe what changes were made
- Explain why the changes are needed
- Reference related issues
- Include testing instructions
- Add screenshots for UI changes

### Review Process
- Maintainers will review within 1-2 weeks
- Address feedback promptly
- Be open to suggestions and changes
- Maintain professional communication

## 🏗️ Architecture Guidelines

### Adding New Agents
- Inherit from base agent patterns
- Implement consistent error handling
- Add proper logging
- Include configuration options

### UI Components
- Follow existing component structure
- Maintain consistent styling
- Ensure accessibility
- Test across browsers

### API Integrations
- Use the unified LLM client pattern
- Implement proper error handling
- Add configuration options
- Include rate limiting

## 🤝 Community Guidelines

### Code of Conduct
- Be respectful and inclusive
- Welcome newcomers
- Provide constructive feedback
- Focus on the project goals

### Communication
- Use clear, professional language
- Be patient with questions
- Share knowledge and expertise
- Collaborate effectively

## 📞 Getting Help

- Open an issue for questions
- Check existing documentation
- Review similar implementations
- Ask for clarification when needed

## 🎉 Recognition

Contributors will be recognized in:
- README.md contributors section
- Release notes for significant contributions
- Project documentation
- Community discussions

Thank you for contributing to the Clinical TLF Automation System!
