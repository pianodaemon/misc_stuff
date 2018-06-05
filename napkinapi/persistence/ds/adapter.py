from abc import ABCMeta, abstractmethod


class AdapterException(Exception):
     """
     Database adapter exception
     """

     def __init__(self, msg = None):
          self.message = msg

     def __str__(self):
          return self.message


class Adapter(metaclass=ABCMeta):
    """
    Database adapter base class.

    Defines the standard methods for coupling the context class to
    the specific database implementation
    """

    def  __init__(self, logger, *args, **kwargs):
        self.logger = logger


    def __str__(self):
        return self.__class__.__name__


    @abstractmethod
    def open(self):
        """Open database connection"""


    @abstractmethod
    def release(self):
        """Release database connection"""
