from textwrap import dedent


def expected(args):
    header = """\
    [STABLE]
    RESOURCE REVISION COMMENT
    """

    """
    foo      22       Stable release 1.3.0
    bar      3
    baz      15
    """

    e = dedent(header)

    for resource, res_v in args['resource'].items():
        v = res_v['stable']
        if 'comment' in v:
            e += '{resource}      {revision}       {comment}\n'.format(
                resource=resource, **v)
        else:
            e += '{resource}      {revision}\n'.format(
                resource=resource, **v)

    return e
