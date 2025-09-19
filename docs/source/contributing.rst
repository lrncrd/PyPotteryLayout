Contributing Guide
==================

We welcome contributions to PyPotteryLayout! This guide explains how to contribute.

Getting Started
---------------

Development Setup
~~~~~~~~~~~~~~~~~

1. **Fork the repository** on GitHub
2. **Clone your fork**::

    git clone https://github.com/YOUR_USERNAME/PyPotteryLayout.git
    cd PyPotteryLayout

3. **Create virtual environment**::

    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate

4. **Install in development mode**::

    pip install -r requirements.txt
    pip install -e .

5. **Create feature branch**::

    git checkout -b feature-name

Code Style
----------

Python Guidelines
~~~~~~~~~~~~~~~~~

* Follow PEP 8 style guide
* Use meaningful variable names
* Add docstrings to all functions
* Keep functions focused and small
* Write self-documenting code

Docstring Format
~~~~~~~~~~~~~~~~

.. code-block:: python

    def function_name(param1, param2):
        """
        Brief description of function.

        Args:
            param1 (type): Description of param1
            param2 (type): Description of param2

        Returns:
            type: Description of return value

        Raises:
            ExceptionType: When this exception occurs
        """

Testing
-------

Running Tests
~~~~~~~~~~~~~

Execute tests with::

    pytest tests/

Writing Tests
~~~~~~~~~~~~~

* Write tests for new features
* Maintain existing test coverage
* Use descriptive test names
* Test edge cases

Submitting Changes
------------------

Pull Request Process
~~~~~~~~~~~~~~~~~~~~

1. **Update documentation** for changes
2. **Add tests** for new features
3. **Ensure tests pass** locally
4. **Commit with clear messages**
5. **Push to your fork**
6. **Create Pull Request** on GitHub

Commit Messages
~~~~~~~~~~~~~~~

Format::

    type: Brief description (50 chars max)

    Longer explanation if needed. Wrap at 72 characters.
    Explain what and why, not how.

    - Bullet points for multiple changes
    - Keep related changes together

Types:

* feat: New feature
* fix: Bug fix
* docs: Documentation only
* style: Code style changes
* refactor: Code restructuring
* test: Test additions/changes
* chore: Build/auxiliary changes

Areas for Contribution
-----------------------

Current Needs
~~~~~~~~~~~~~

* **Documentation**: Tutorials, examples, translations
* **Testing**: Unit tests, integration tests
* **Features**: New layout algorithms, export formats
* **Bug Fixes**: Check GitHub issues
* **Performance**: Optimization for large datasets
* **UI/UX**: Interface improvements

Feature Ideas
~~~~~~~~~~~~~

* Additional layout modes
* More metadata formats
* Export format options
* Batch processing tools
* Command-line interface
* Web-based version

Reporting Issues
----------------

Bug Reports
~~~~~~~~~~~

Include:

1. System information (OS, Python version)
2. Steps to reproduce
3. Expected behavior
4. Actual behavior
5. Error messages/logs
6. Sample data if applicable

Feature Requests
~~~~~~~~~~~~~~~~

Describe:

1. Use case/problem solved
2. Proposed solution
3. Alternative approaches
4. Mockups/examples if applicable

Community
---------

Communication
~~~~~~~~~~~~~

* GitHub Issues: Bug reports, features
* Discussions: General questions
* Pull Requests: Code contributions

Code of Conduct
~~~~~~~~~~~~~~~

* Be respectful and inclusive
* Welcome newcomers
* Provide constructive feedback
* Focus on what's best for the community
* Show empathy towards others

License
-------

By contributing, you agree that your contributions will be licensed under the same license as the project (MIT License).

Recognition
-----------

Contributors are recognized in:

* GitHub contributors page
* README acknowledgments
* Release notes

Thank you for contributing to PyPotteryLayout!