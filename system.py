#!/usr/bin/python

class RunCommand:
    '''
    Run a command and catch it's output in tempfile.SpooledTemporaryFile. Then read those files into memory.
    '''

    import re, subprocess, tempfile

    def __init__( self, cmd ):
        '''
        Argument cmd should be list of args like call to subprocess.call(), which this class
        wraps.
        '''

        self.command = cmd

        self.out = []
        self.err = []

        self._runCommand()

    def _runCommand( self ):
        '''
        Perform subprocess.call() call and catch the output.
        '''

        tmp_out = self.tempfile.SpooledTemporaryFile()
        tmp_err = self.tempfile.SpooledTemporaryFile()

        self.exit = self.subprocess.call( self.command, stdout=tmp_out, stderr=tmp_err )

        tmp_out.seek(0); tmp_err.seek(0)

        self.out = tmp_out.readlines()
        self.err = tmp_err.readlines()

        tmp_out.close(); tmp_err.close() 

    def strip( self ):
        '''
        May as well provide features.
        '''
        for i in range( len( self.out ) ):
            self.out[ i ] = self.out[ i ].strip()
        for i in range( len( self.err ) ):
            self.err[ i ] = self.err[ i ].strip()
        return self

    def filter( self, regex_string ):
        '''
        But not this many right now...
        '''
        pass

    def getExit( self ):
        '''
        Get the exit status of command.
        '''
        return self.exit

    def getOut( self ):
        '''
        Get the stdout output (if any) of the command.
        '''
        return self.out

    def getErr( self ):
        '''
        Get the stderr output (if any) of the command.
        '''
        return self.err

    def iterOut( self ):
        '''
        Iterate over command's stdout output.
        '''
        for l in self.out: yield l

    def iterErr( self ):
        '''
        Iterate over command's stderr output.
        '''
        for l in self.err: yield l

