class MarkError(Exception): pass

class CLIError(MarkError): pass

class MarkfileError(MarkError): pass

class QueryError(MarkError): pass

class TemplateVariableError(MarkError): pass

