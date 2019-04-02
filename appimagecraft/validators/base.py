from typing import List


class ValidatorBase:
    def __init__(self):
        # make sure validator is available, otherwise refuse instantiation
        if not self.is_available():
            raise RuntimeError("validator {} not available".format(self.__class__))

    @staticmethod
    def supported_file_types() -> List[str]:
        """
        Fetch fnmatch patterns of supported file types. Can be used by a factory function to auto-create a suitable
        validator based on the file name.

        :return: matching validator or None
        :rtype: ValidatorBase
        """

        raise NotImplementedError

    @staticmethod
    def is_available() -> bool:
        """
        Check if the validator is available on this platform, i.e., required external tools are installed, etc.

        :return: whether validator can be used
        """

        raise NotImplementedError

    def validate(self, path: str):
        """
        Perform validation.

        :param path: path to file that shall be validated
        :raises ValidationError: in case validation fails
        """

        raise NotImplementedError
