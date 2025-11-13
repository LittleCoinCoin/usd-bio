# Contributing to USD-Bio

Thank you for your interest in contributing to USD-Bio!

## Development Setup

See [Building USD-Bio](docs/developer_guide/building.rst) for complete setup instructions.

## Contribution Workflow

### 1. Branch Naming Convention

Follow the project's milestone-based branching strategy:

- **Milestone branches**: `milestone/<milestone-id>-<description>`
  - Example: `milestone/2.1-schema-definition`
- **Task branches**: `task/<task-id>-<description>`
  - Example: `task/2.1.1-molecular-schema`
- **Bug fix branches**: `fix/<issue-number>-<description>`
  - Example: `fix/42-memory-leak`

### 2. Commit Message Format

Use [Conventional Commits](https://www.conventionalcommits.org/):

```
<type>(<scope>): <description>

[optional body]

[optional footer]
```

**Types**:
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `test`: Test additions or modifications
- `refactor`: Code refactoring
- `chore`: Build system or dependency updates
- `ci`: CI/CD configuration changes

**Examples**:
```
feat(schema): add molecular data USD schema
test(processor): add unit tests for stage creation
docs(api): document UsdBioProcessor class
fix(build): correct CMake find_package for GTest
```

### 3. Code Standards

**C++ Style**:
- C++20 standard
- Follow [OpenUSD Coding Guidelines](https://openusd.org/release/contributing_to_usd.html)
- Use meaningful variable and function names
- Avoid abbreviations except standard ones (USD, API, etc.)

**Documentation**:
- Doxygen comments for all public APIs
- Brief description with `\brief`
- Parameter documentation with `\param`
- Return value documentation with `\return`

Example:
```cpp
/// \brief Process biology data and add metadata to USD stage
/// \param stage The USD stage to modify
/// \param data Biology data to process
/// \return True if processing succeeded, false otherwise
bool ProcessBiologyData(UsdStageRefPtr stage, const BioData& data);
```

**Testing**:
- Unit tests for all new features
- Use Google Test framework
- Aim for >90% code coverage
- Tests must pass before PR approval

### 4. Pull Request Process

1. **Create PR** against `dev` branch (not `main`)
2. **Title**: Use conventional commit format
3. **Description**: 
   - What changes were made
   - Why (link to issue if applicable)
   - Testing performed
   - Documentation updated
4. **Checks**: Ensure CI/CD passes (build + tests)
5. **Review**: Address reviewer feedback
6. **Merge**: Squash and merge after approval

## Code Review Guidelines

**For Contributors**:
- Keep PRs focused and reasonably sized
- Respond to feedback promptly
- Update based on review comments

**For Reviewers**:
- Verify code follows style guide
- Check test coverage
- Validate documentation updates
- Test locally if significant changes

## Questions?

- Open a GitHub Discussion for general questions
- Comment on relevant Issues for specific problems
- Tag maintainers for urgent matters

---

Thank you for contributing to USD-Bio! 🧬
