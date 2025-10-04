# ADB-UTIL File Structure Migration Plan

## 📋 Overview

This document provides a comprehensive migration plan to restructure the ADB-UTIL project for better maintainability, scalability, and modern Python practices. The migration is divided into 5 phases, each with specific tasks and detailed prompts.

## 🎯 Migration Goals

- **Modernize** the project structure following Python best practices
- **Improve** code organization and separation of concerns
- **Enhance** testing capabilities and coverage
- **Streamline** build and deployment processes
- **Facilitate** future development and contributions

## 📊 Migration Phases Overview

| Phase | Duration | Priority | Complexity | Description |
|-------|----------|----------|------------|-------------|
| 1 | 1-2 days | High | Low | Clean up root directory and modernize packaging |
| 2 | 3-5 days | High | Medium | Reorganize source code structure |
| 3 | 2-3 days | Medium | Medium | Restructure tests and add coverage |
| 4 | 2-3 days | Medium | Low | Add configuration and asset management |
| 5 | 3-4 days | Low | High | Implement advanced features |

---

## 🚀 Phase 1: Foundation Cleanup & Modern Packaging

### Duration: 1-2 days
### Priority: High
### Complexity: Low

### Objectives
- Clean up root directory structure
- Implement modern Python packaging
- Separate development and production dependencies
- Set up proper virtual environment management

### Tasks

#### 1.1 Root Directory Cleanup
**Prompt:**
```
Clean up the root directory of the adb-util project by:

1. Remove duplicate virtual environment directories (keep only .venv/)
2. Move build artifacts to a separate build/ directory
3. Create proper directory structure:
   - scripts/ (for build and utility scripts)
   - config/ (for configuration files)
   - assets/ (for static assets)
   - dist/ (for distribution builds)

4. Update .gitignore to exclude:
   - build/
   - dist/
   - .venv/
   - *.pyc
   - __pycache__/
   - .pytest_cache/
   - .mypy_cache/

5. Remove any temporary files and organize remaining files logically
```

#### 1.2 Modern Python Packaging Setup
**Prompt:**
```
Create modern Python packaging for adb-util:

1. Create pyproject.toml with:
   - Build system configuration
   - Project metadata (name, version, description, authors)
   - Dependencies (PyQt6, qasync, aiofiles, psutil, watchdog)
   - Optional dev dependencies (pytest, black, flake8, mypy)
   - Project scripts entry point
   - Tool configurations (black, mypy, setuptools)

2. Create setup.py for backward compatibility if needed

3. Split requirements.txt into:
   - requirements/base.txt (production dependencies)
   - requirements/dev.txt (development dependencies)
   - requirements/prod.txt (production-specific overrides)

4. Update README.md with new installation instructions using pip install -e .
```

#### 1.3 Virtual Environment Standardization
**Prompt:**
```
Standardize virtual environment setup:

1. Create a single .venv/ directory in the root
2. Create scripts/dev/setup_dev.py to automate:
   - Virtual environment creation
   - Dependency installation
   - Development environment setup

3. Update documentation to use consistent venv commands:
   - python -m venv .venv
   - .venv/Scripts/activate (Windows)
   - source .venv/bin/activate (Linux/macOS)

4. Create .python-version file for pyenv users
5. Add pre-commit hooks configuration if desired
```

### Deliverables
- [ ] Clean root directory structure
- [ ] pyproject.toml with proper configuration
- [ ] Split requirements files
- [ ] Updated .gitignore
- [ ] Standardized virtual environment setup
- [ ] Updated documentation

### Validation
- [ ] Project can be installed with `pip install -e .`
- [ ] All dependencies install correctly
- [ ] Development environment setup works
- [ ] No duplicate virtual environments

---

## 🏗️ Phase 2: Source Code Reorganization

### Duration: 3-5 days
### Priority: High
### Complexity: Medium

### Objectives
- Reorganize source code into a proper package structure
- Implement clear separation of concerns
- Improve module organization and naming
- Maintain backward compatibility during transition

### Tasks

#### 2.1 Create New Package Structure
**Prompt:**
```
Reorganize the src/ directory into a proper Python package structure:

1. Create src/adb_util/ as the main package directory
2. Move all existing modules into the new structure:
   - src/adb/ → src/adb_util/core/device/ and src/adb_util/core/commands/
   - src/gui/ → src/adb_util/ui/
   - src/services/ → src/adb_util/services/
   - src/models/ → src/adb_util/models/
   - src/utils/ → src/adb_util/utils/

3. Create proper __init__.py files for each package
4. Split large modules into smaller, focused modules:
   - device_manager.py → manager.py, discovery.py, monitoring.py
   - command_runner.py → runner.py, executor.py, shell.py
   - file_operations.py → transfer.py, sync.py, operations.py

5. Update all import statements to use the new package structure
6. Create src/adb_util/__main__.py as the new entry point
```

#### 2.2 Refactor Core Modules
**Prompt:**
```
Refactor core modules for better separation of concerns:

1. Split src/adb_util/core/device/manager.py into:
   - manager.py (main DeviceManager class)
   - discovery.py (device discovery logic)
   - monitoring.py (device monitoring and status updates)
   - properties.py (device property extraction)

2. Split src/adb_util/core/commands/runner.py into:
   - runner.py (main CommandRunner class)
   - executor.py (command execution logic)
   - shell.py (shell command handling)
   - parser.py (command output parsing)

3. Create src/adb_util/core/file_ops/ with:
   - transfer.py (file transfer operations)
   - sync.py (file synchronization)
   - operations.py (file system operations)
   - validation.py (file operation validation)

4. Ensure each module has a single responsibility
5. Update imports and dependencies accordingly
```

#### 2.3 Reorganize UI Components
**Prompt:**
```
Reorganize UI components for better modularity:

1. Create src/adb_util/ui/main/ with:
   - window.py (MainWindow class)
   - application.py (QApplication setup and configuration)

2. Create src/adb_util/ui/components/ with:
   - device_tab.py (device management UI)
   - file_manager.py (file operations UI)
   - terminal.py (terminal interface)
   - logcat_viewer.py (logcat viewing)
   - script_editor.py (script editing)

3. Create src/adb_util/ui/dialogs/ with:
   - preferences.py (preferences dialog)
   - script_dialog.py (script editing dialog)
   - about.py (about dialog)

4. Create src/adb_util/ui/widgets/ with:
   - device_list.py (device list widget)
   - file_browser.py (file browser widget)
   - log_viewer.py (log viewer widget)
   - command_history.py (command history widget)

5. Update all UI imports and references
```

#### 2.4 Update Entry Point and Main Module
**Prompt:**
```
Update the application entry point and main module:

1. Create src/adb_util/__main__.py:
   - Move main() function from main.py
   - Update imports to use new package structure
   - Handle both development and PyInstaller environments

2. Create src/adb_util/app.py:
   - Application factory function
   - Configuration setup
   - Dependency injection setup

3. Update main.py in root to:
   - Import from adb_util.__main__
   - Maintain backward compatibility
   - Provide clear deprecation message

4. Update pyproject.toml scripts section:
   - adb-util = "adb_util.__main__:main"

5. Test that the application still runs correctly
```

### Deliverables
- [ ] New package structure under src/adb_util/
- [ ] Refactored core modules with single responsibilities
- [ ] Reorganized UI components
- [ ] Updated entry point and main module
- [ ] All imports updated to new structure
- [ ] Application functionality preserved

### Validation
- [ ] Application starts and runs correctly
- [ ] All features work as before
- [ ] No import errors
- [ ] Code passes linting and type checking
- [ ] Tests still pass (if any exist)

---

## 🧪 Phase 3: Test Restructuring & Coverage

### Duration: 2-3 days
### Priority: Medium
### Complexity: Medium

### Objectives
- Restructure test organization to match new source structure
- Add comprehensive test coverage
- Implement proper test fixtures and utilities
- Set up continuous integration test structure

### Tasks

#### 3.1 Restructure Test Organization
**Prompt:**
```
Restructure the tests/ directory to match the new source structure:

1. Create new test directory structure:
   - tests/unit/core/ (unit tests for core modules)
   - tests/unit/ui/ (unit tests for UI components)
   - tests/unit/services/ (unit tests for services)
   - tests/unit/models/ (unit tests for models)
   - tests/unit/utils/ (unit tests for utilities)

2. Move existing tests to appropriate locations:
   - tests/adb/ → tests/unit/core/device/
   - tests/gui/ → tests/unit/ui/
   - tests/services/ → tests/unit/services/
   - tests/models/ → tests/unit/models/
   - tests/utils/ → tests/unit/utils/

3. Create tests/integration/ for integration tests:
   - device_workflows.py (end-to-end device operations)
   - file_operations.py (file transfer workflows)
   - ui_workflows.py (UI interaction workflows)

4. Create tests/e2e/ for end-to-end tests:
   - gui_tests.py (complete GUI workflows)
   - device_tests.py (real device testing)

5. Update all test imports to use new package structure
```

#### 3.2 Enhance Test Fixtures and Utilities
**Prompt:**
```
Enhance test fixtures and create comprehensive test utilities:

1. Expand tests/fixtures/ with:
   - devices.py (device mock objects and test data)
   - commands.py (command execution mocks)
   - configs.py (configuration test data)
   - ui.py (UI component test fixtures)
   - files.py (file system test fixtures)

2. Create tests/helpers/ with:
   - mock_adb.py (ADB command mocking utilities)
   - mock_devices.py (device simulation helpers)
   - ui_helpers.py (UI testing utilities)
   - async_helpers.py (async test utilities)

3. Update tests/conftest.py with:
   - Comprehensive pytest configuration
   - Global fixtures for common test setup
   - Async test configuration
   - Qt application fixtures for UI tests

4. Create tests/utils/ with:
   - test_data.py (test data generators)
   - assertions.py (custom assertions)
   - decorators.py (test decorators)
```

#### 3.3 Add Comprehensive Test Coverage
**Prompt:**
```
Add comprehensive test coverage for all modules:

1. Create unit tests for all core modules:
   - Device discovery and management
   - Command execution and parsing
   - File operations and transfers
   - Logcat handling and filtering

2. Create UI component tests:
   - Widget functionality tests
   - Event handling tests
   - Layout and styling tests
   - User interaction tests

3. Create service layer tests:
   - Configuration management
   - Command storage
   - Script management
   - Theme management

4. Create integration tests:
   - Device workflow tests
   - File operation workflows
   - UI interaction workflows
   - Error handling workflows

5. Set up test coverage reporting:
   - Configure pytest-cov
   - Set coverage thresholds
   - Generate coverage reports
   - Add coverage badges to README
```

#### 3.4 Set Up Test Automation
**Prompt:**
```
Set up comprehensive test automation:

1. Create scripts/dev/run_tests.py with options for:
   - Unit tests only
   - Integration tests only
   - Full test suite
   - Coverage reporting
   - Parallel test execution

2. Add GitHub Actions workflow for:
   - Automated testing on PR
   - Coverage reporting
   - Linting and type checking
   - Multi-platform testing

3. Create tests/performance/ for performance tests:
   - device_discovery_performance.py
   - logcat_streaming_performance.py
   - file_transfer_performance.py

4. Set up test data management:
   - Create tests/data/ for test files
   - Add data cleanup utilities
   - Implement test data versioning

5. Configure test reporting:
   - HTML coverage reports
   - JUnit XML for CI integration
   - Performance benchmark reports
```

### Deliverables
- [ ] Restructured test directory matching source structure
- [ ] Enhanced test fixtures and utilities
- [ ] Comprehensive test coverage for all modules
- [ ] Test automation scripts and CI configuration
- [ ] Performance test suite
- [ ] Coverage reporting setup

### Validation
- [ ] All tests pass
- [ ] Test coverage meets target thresholds (80%+)
- [ ] CI pipeline works correctly
- [ ] Performance tests establish baselines
- [ ] Test data is properly managed

---

## ⚙️ Phase 4: Configuration & Asset Management

### Duration: 2-3 days
### Priority: Medium
### Complexity: Low

### Objectives
- Centralize configuration management
- Organize static assets properly
- Implement configuration validation
- Set up theme and resource management

### Tasks

#### 4.1 Configuration Management Setup
**Prompt:**
```
Set up comprehensive configuration management:

1. Create config/ directory structure:
   - config/default/ (default configuration files)
   - config/templates/ (configuration templates)
   - config/schemas/ (configuration validation schemas)
   - config/examples/ (example configurations)

2. Create default configuration files:
   - settings.yaml (main application settings)
   - themes.yaml (theme configurations)
   - keybindings.yaml (keyboard shortcuts)
   - devices.yaml (device-specific settings)

3. Implement configuration validation:
   - Create JSON schemas for all config files
   - Add configuration validation in ConfigManager
   - Implement configuration migration for version updates
   - Add configuration backup and restore

4. Update ConfigManager to support:
   - YAML configuration files
   - Environment variable overrides
   - User-specific configuration inheritance
   - Configuration hot-reloading

5. Create configuration utilities:
   - config/scripts/validate_config.py
   - config/scripts/migrate_config.py
   - config/scripts/reset_config.py
```

#### 4.2 Asset Organization
**Prompt:**
```
Organize static assets and resources:

1. Create assets/ directory structure:
   - assets/icons/ (application icons)
   - assets/themes/ (UI themes)
   - assets/resources/ (application resources)
   - assets/samples/ (sample files and data)

2. Organize icons by category:
   - assets/icons/app/ (application icons)
   - assets/icons/devices/ (device status icons)
   - assets/icons/actions/ (action button icons)
   - assets/icons/status/ (status indicator icons)

3. Create theme system:
   - assets/themes/light/ (light theme resources)
   - assets/themes/dark/ (dark theme resources)
   - assets/themes/custom/ (custom theme templates)
   - Update ThemeManager to use asset-based themes

4. Organize resources:
   - assets/resources/translations/ (i18n files)
   - assets/resources/help/ (help documentation)
   - assets/resources/samples/ (sample scripts and configs)

5. Update build system to include assets:
   - Modify PyInstaller spec to include assets
   - Create asset packaging scripts
   - Add asset validation utilities
```

#### 4.3 Resource Management System
**Prompt:`
```
Implement comprehensive resource management:

1. Create src/adb_util/resources/ module:
   - manager.py (ResourceManager class)
   - loader.py (resource loading utilities)
   - validator.py (resource validation)
   - cache.py (resource caching)

2. Implement resource loading system:
   - Support for multiple resource types (icons, themes, translations)
   - Resource path resolution (development vs production)
   - Resource caching and optimization
   - Fallback resource handling

3. Create resource utilities:
   - scripts/resources/build_resources.py
   - scripts/resources/validate_resources.py
   - scripts/resources/optimize_resources.py

4. Update UI components to use ResourceManager:
   - Replace hardcoded paths with resource manager calls
   - Implement dynamic theme switching
   - Add resource-aware icon loading

5. Add resource testing:
   - Create tests for resource loading
   - Validate all resources are accessible
   - Test resource fallback mechanisms
```

#### 4.4 Theme and Styling System
**Prompt:`
```
Enhance theme and styling system:

1. Expand ThemeManager capabilities:
   - Support for multiple theme formats (CSS, QSS, YAML)
   - Dynamic theme switching without restart
   - Custom theme creation and editing
   - Theme preview functionality

2. Create comprehensive theme system:
   - Base theme templates
   - Component-specific styling
   - Responsive design elements
   - Accessibility considerations

3. Implement theme utilities:
   - scripts/themes/generate_theme.py
   - scripts/themes/validate_theme.py
   - scripts/themes/preview_theme.py

4. Add theme customization UI:
   - Theme selection dialog
   - Color picker integration
   - Font size adjustment
   - Custom theme editor

5. Create theme documentation:
   - Theme development guide
   - Custom theme creation tutorial
   - Theme API documentation
```

### Deliverables
- [ ] Centralized configuration management
- [ ] Organized asset directory structure
- [ ] Resource management system
- [ ] Enhanced theme and styling system
- [ ] Configuration validation and migration
- [ ] Asset packaging and optimization

### Validation
- [ ] All configurations load correctly
- [ ] Assets are accessible in both development and production
- [ ] Theme switching works without issues
- [ ] Configuration validation catches errors
- [ ] Resource loading is efficient and reliable

---

## 🚀 Phase 5: Advanced Features & Polish

### Duration: 3-4 days
### Priority: Low
### Complexity: High

### Objectives
- Add command-line interface
- Implement internationalization support
- Add plugin system architecture
- Enhance developer experience tools

### Tasks

#### 5.1 Command-Line Interface
**Prompt:`
```
Implement comprehensive command-line interface:

1. Create src/adb_util/cli/ module:
   - main.py (CLI entry point)
   - commands/ (CLI command modules)
   - utils.py (CLI utilities)
   - formatters.py (output formatting)

2. Implement core CLI commands:
   - device list (list connected devices)
   - device info (show device information)
   - logcat stream (stream device logs)
   - file push/pull (file operations)
   - script run (execute scripts)

3. Add CLI features:
   - Interactive mode with command completion
   - Output formatting (JSON, YAML, table)
   - Verbose and quiet modes
   - Configuration file support

4. Create CLI documentation:
   - Command reference
   - Usage examples
   - Integration guides

5. Add CLI testing:
   - Unit tests for CLI commands
   - Integration tests for CLI workflows
   - Performance tests for CLI operations
```

#### 5.2 Internationalization Support
**Prompt:`
```
Implement internationalization (i18n) support:

1. Set up i18n infrastructure:
   - Add gettext support
   - Create translation file structure
   - Implement locale detection
   - Add language switching

2. Create translation management:
   - scripts/i18n/extract_strings.py
   - scripts/i18n/update_translations.py
   - scripts/i18n/validate_translations.py

3. Implement UI translation:
   - Update all UI strings to use translation functions
   - Add language selection to preferences
   - Implement dynamic language switching
   - Handle RTL language support

4. Create initial translations:
   - English (base language)
   - Spanish (example translation)
   - French (example translation)

5. Add translation testing:
   - Test translation completeness
   - Validate translation quality
   - Test language switching functionality
```

#### 5.3 Plugin System Architecture
**Prompt:`
```
Design and implement plugin system:

1. Create plugin architecture:
   - src/adb_util/plugins/ (plugin system)
   - plugin_manager.py (plugin management)
   - base_plugin.py (plugin base class)
   - plugin_registry.py (plugin registry)

2. Define plugin interfaces:
   - Device plugins (device-specific functionality)
   - Command plugins (custom commands)
   - UI plugins (UI extensions)
   - File operation plugins (custom file operations)

3. Implement plugin loading:
   - Dynamic plugin discovery
   - Plugin dependency management
   - Plugin configuration system
   - Plugin security and validation

4. Create plugin development tools:
   - Plugin template generator
   - Plugin testing framework
   - Plugin documentation generator
   - Plugin packaging utilities

5. Add example plugins:
   - Device info plugin
   - Custom command plugin
   - UI theme plugin
   - File format plugin
```

#### 5.4 Developer Experience Enhancements
**Prompt:`
```
Enhance developer experience and tooling:

1. Create comprehensive development scripts:
   - scripts/dev/setup_dev.py (complete dev setup)
   - scripts/dev/reset_dev.py (reset development environment)
   - scripts/dev/check_dev.py (validate dev environment)
   - scripts/dev/update_deps.py (update dependencies)

2. Add code generation tools:
   - scripts/generate/component.py (generate UI components)
   - scripts/generate/test.py (generate test templates)
   - scripts/generate/plugin.py (generate plugin templates)

3. Implement development utilities:
   - Debug mode with enhanced logging
   - Development configuration profiles
   - Hot-reload for configuration changes
   - Development data seeding

4. Create development documentation:
   - Developer setup guide
   - Code style guide
   - Architecture documentation
   - Contributing guidelines

5. Add development testing:
   - Development environment validation
   - Code quality checks
   - Performance regression testing
   - Documentation validation
```

### Deliverables
- [ ] Command-line interface with core commands
- [ ] Internationalization support with translation management
- [ ] Plugin system architecture with examples
- [ ] Enhanced developer experience tools
- [ ] Comprehensive development documentation
- [ ] Advanced testing and validation

### Validation
- [ ] CLI commands work correctly
- [ ] Language switching functions properly
- [ ] Plugin system loads and manages plugins
- [ ] Development tools streamline workflow
- [ ] All new features are properly tested
- [ ] Documentation is complete and accurate

---

## 📋 Migration Checklist

### Pre-Migration
- [ ] Create backup of current project
- [ ] Ensure all current tests pass
- [ ] Document current functionality
- [ ] Set up development branch for migration

### Phase 1: Foundation
- [ ] Clean root directory structure
- [ ] Create pyproject.toml
- [ ] Split requirements files
- [ ] Set up single virtual environment
- [ ] Update documentation

### Phase 2: Source Reorganization
- [ ] Create new package structure
- [ ] Refactor core modules
- [ ] Reorganize UI components
- [ ] Update entry point
- [ ] Verify functionality preservation

### Phase 3: Test Restructuring
- [ ] Restructure test organization
- [ ] Enhance test fixtures
- [ ] Add comprehensive coverage
- [ ] Set up test automation
- [ ] Validate test suite

### Phase 4: Configuration & Assets
- [ ] Set up configuration management
- [ ] Organize assets
- [ ] Implement resource management
- [ ] Enhance theme system
- [ ] Validate configuration system

### Phase 5: Advanced Features
- [ ] Implement CLI interface
- [ ] Add internationalization
- [ ] Create plugin system
- [ ] Enhance developer tools
- [ ] Complete documentation

### Post-Migration
- [ ] Run full test suite
- [ ] Validate all features work
- [ ] Update deployment scripts
- [ ] Create migration summary
- [ ] Plan future improvements

---

## 🚨 Risk Mitigation

### Potential Risks
1. **Breaking Changes**: Import path changes may break existing code
2. **Testing Gaps**: Restructuring may temporarily reduce test coverage
3. **Configuration Loss**: User configurations may be lost during migration
4. **Build Issues**: New packaging may cause build/deployment issues
5. **Performance Regression**: Restructuring may impact performance

### Mitigation Strategies
1. **Gradual Migration**: Implement changes incrementally with validation
2. **Comprehensive Testing**: Maintain test coverage throughout migration
3. **Configuration Backup**: Automatically backup and migrate user configs
4. **Build Validation**: Test builds at each phase
5. **Performance Monitoring**: Monitor performance throughout migration

---

## 📈 Success Metrics

### Phase 1 Success Criteria
- [ ] Project installs with `pip install -e .`
- [ ] All dependencies resolve correctly
- [ ] Development environment setup works
- [ ] No duplicate virtual environments

### Phase 2 Success Criteria
- [ ] Application functionality preserved
- [ ] All imports work correctly
- [ ] Code passes linting and type checking
- [ ] Modular structure is clear and logical

### Phase 3 Success Criteria
- [ ] Test coverage > 80%
- [ ] All tests pass consistently
- [ ] CI pipeline works correctly
- [ ] Test organization is clear

### Phase 4 Success Criteria
- [ ] Configuration system is robust
- [ ] Assets load correctly in all environments
- [ ] Theme system is flexible and reliable
- [ ] Resource management is efficient

### Phase 5 Success Criteria
- [ ] CLI is functional and user-friendly
- [ ] Internationalization works correctly
- [ ] Plugin system is extensible
- [ ] Developer experience is improved

---

## 📚 Additional Resources

### Documentation to Create
- [ ] Migration guide for contributors
- [ ] New architecture documentation
- [ ] Plugin development guide
- [ ] CLI usage documentation
- [ ] Configuration reference

### Tools to Set Up
- [ ] Pre-commit hooks
- [ ] Automated dependency updates
- [ ] Code quality monitoring
- [ ] Performance benchmarking
- [ ] Documentation generation

---

*This migration plan provides a comprehensive roadmap for restructuring the ADB-UTIL project. Each phase builds upon the previous one, ensuring a smooth transition while maintaining project stability and functionality.*
