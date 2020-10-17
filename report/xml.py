"""Module provides a set of API for XML files."""
import logging
from abc import ABC, abstractmethod
from types import TracebackType
from typing import Optional, Type
from typing import Dict, Iterator
from junitparser import JUnitXml, TestCase as JCase, TestSuite as JSuite

_logger: logging.Logger = logging.getLogger(__name__)


class _Outcome:
    """An outcome of report_from."""

    def __init__(self, report: JUnitXml) -> None:
        self._report: JUnitXml = report

    @property
    def total(self) -> int:
        """Returns total tests count."""
        return self._report.tests

    @property
    def skipped(self) -> int:
        """Returns skipped tests count."""
        return self._report.skipped

    @property
    def failed(self) -> int:
        """Returns failed tests count."""
        return self._report.failures

    @property
    def errored(self) -> int:
        """Returns errored tests count."""
        return self._report.errors

    @property
    def passed(self) -> int:
        """Returns passed tests count."""
        return self.total - self.skipped - self.failed - self.errored

    def as_dict(self) -> Dict[str, int]:
        """Returns tests as dict."""
        return {
            'total': self.total,
            'skipped': self.skipped,
            'failed': self.failed,
            'errored': self.errored,
            'passed': self.passed,
        }


class _Testcase:
    """Testcase from xml file."""

    def __init__(self, case: JCase) -> None:
        self._case = case

    def status(self) -> str:
        """Returns testcase status."""
        if self._case.result is None:
            return 'Passed'
        return 'Failed'

    def name(self, suite_prefix: bool = False) -> str:
        """Returns testcase name."""
        if not suite_prefix:
            return self._case.name
        return f'{self._case.classname}:{self._case.name}'


class _Testsuite(Iterator[_Testcase]):
    """Testsuite from xml file."""

    def __init__(self, suite: JSuite) -> None:
        self._suite = suite
        self._iter_suite = iter(suite)

    def __iter__(self) -> Iterator[_Testcase]:
        """Returns testcases iterator."""
        return self

    def __next__(self) -> _Testcase:
        """Returns a testcase."""
        return _Testcase(next(self._iter_suite))

    def __len__(self) -> int:
        """Count of testcases."""
        return len(self._suite)

    def name(self) -> str:
        """Testsuite name."""
        return self._suite.name


class _Testsuites(Iterator[_Testsuite]):
    """Testsuites from xml file."""

    def __init__(self, xml: JUnitXml) -> None:
        self._xml = xml
        self._suites = iter(xml)

    def __iter__(self) -> Iterator[_Testsuite]:
        """Returns testsuites iterator."""
        return self

    def __next__(self) -> _Testsuite:
        """Returns a testsuite."""
        return _Testsuite(next(self._suites))

    def __len__(self) -> int:
        """Count of testsuites."""
        return len(self._xml)

    def name(self) -> str:
        """Testsuites name."""
        return self._xml.name


class TestXml(ABC):
    """XML file abstraction."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Returns name of xml file."""
        pass

    @property
    @abstractmethod
    def outcome(self) -> _Outcome:
        """Returns test results outcome."""
        pass

    @property
    @abstractmethod
    def testsuites(self) -> _Testsuites:
        """Returns test suites from xml file."""
        pass


class _TestXmlFromJUnit(TestXml):
    """XML file from junit source."""

    def __init__(self, xml: JUnitXml) -> None:
        self._xml = xml
        self._testsuites: _Testsuites = _Testsuites(xml)
        self._outcome: _Outcome = _Outcome(xml)

    @property
    def name(self) -> str:
        """Returns name of xml file."""
        return self._xml.name

    @property
    def outcome(self) -> _Outcome:
        """Returns test results outcome."""
        return self._outcome

    @property
    def testsuites(self) -> _Testsuites:
        """Returns test suites from xml file."""
        return self._testsuites


class PytestXml(TestXml):
    """Pytest XML file."""

    def __init__(self, path: str) -> None:
        self._xml: TestXml = _TestXmlFromJUnit(JUnitXml.fromfile(path))
        self._path: str = path

    @property
    def name(self) -> str:
        """Returns name of xml file."""
        return self._path

    @property
    def outcome(self) -> _Outcome:
        """Returns pytest results outcome."""
        return self._xml.outcome

    @property
    def testsuites(self) -> _Testsuites:
        """Returns pytest suites from xml file."""
        return self._xml.testsuites


class ReportPage:
    """Represent test report page."""

    def __init__(self, xml: TestXml) -> None:
        self._xml = xml
        self._content: str = ''

    def __enter__(self) -> 'ReportPage':
        """Returns report page instance."""
        if not self._content:
            self._content += self.build_results_table()
        return self

    @property
    def content(self) -> str:
        """Returns report page content."""
        return self._content

    def build_results_table(self) -> str:
        """Returns test run stats."""
        _logger.info('Collecting statistics from "%s" file', self._xml.name)
        return (
            '<h1>Test report:</h1>\n'
            f'Total: {self._xml.outcome.total}\n'
            f'Passed: {self._xml.outcome.passed}\n'
            f'Failed: {self._xml.outcome.failed}\n'
            f'Skipped: {self._xml.outcome.skipped}\n'
            f'Errored: {self._xml.outcome.errored}\n'
        )

    def __exit__(
        self,
        exception_type: Optional[Type[BaseException]],
        exception_value: Optional[BaseException],
        traceback: Optional[TracebackType],
    ) -> None:
        """Clears report page content."""
        self._content = ''
