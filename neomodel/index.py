from .properties import AliasProperty
from .core import cypher_query


class NodeIndexManager(object):
    def __init__(self, node_class, index_name):
        self.node_class = node_class
        self.name = index_name

    def _check_params(self, params):
        """checked args are indexed and convert aliases"""
        for key in params.keys():
            prop = self.node_class.get_property(key)
            if isinstance(prop, AliasProperty):
                real_key = prop.aliased_to()
                if real_key in params:
                    msg = "Can't alias {0} to {1} in {2}, key {0} exists."
                    raise Exception(msg.format(key, real_key, repr(params)))
                params[real_key] = params[key]
                del params[key]

    def _build_query(self, params):
        q = "MATCH (n:{}) WHERE\n".format(self.node_class.__label__)
        q += " AND ".join(["n.{} = {{{}}}".format(key, key) for key in params.keys()])
        return q + " RETURN n"

    def search(self, **kwargs):
        # TODO deprecate index.
        """Search nodes using an via index"""
        if not kwargs:
            msg = "No arguments provided.\nUsage: {0}.index.search(key=val)"
            raise ValueError(msg.format(self.node_class.__name__))
        self._check_params(kwargs)
        results, _ = cypher_query(self._build_query(kwargs), kwargs)
        return [self.node_class.inflate(n) for n in results[0]]

    def get(self, **kwargs):
        """Load single node from index lookup"""
        if not kwargs:
            msg = "No arguments provided.\nUsage: {0}.index.get(key=val)"
            raise ValueError(msg.format(self.node_class.__name__))

        nodes = self.search(**kwargs)
        if len(nodes) == 1:
            return nodes[0]
        elif len(nodes) > 1:
            raise Exception("Multiple nodes returned from query, expected one")
        else:
            raise self.node_class.DoesNotExist("Can't find node in index matching query")
