import gettext
import six


if six.PY2:
    gettext.install('neutron', unicode=1)
else:
    gettext.install('neutron')
