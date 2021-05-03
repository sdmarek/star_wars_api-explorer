import petl as etl
from django.conf import settings
from django.shortcuts import redirect
from django.views.generic import DetailView, ListView
from django_simple_task import defer
from .models import Collection
from .tasks import fetch


class CollectionDetailView(DetailView):
    model = Collection
    template_name = 'collection_detail.html'
    context_object_name = 'collection'

    def get_context_data(self, **kwargs):
        def url(name, value):
            'return present url query with updated name-value pair'
            qd = self.request.GET.copy()
            if value:
                if isinstance(value, type([])):
                    qd.setlist(name, value)
                else:
                    qd[name] = value
            else:
                del qd[name]
            return qd.urlencode()

        def xor(list1, list2):
            return list(set(list1) ^ set(list2))

        context = super().get_context_data(**kwargs)
        csv = str(settings.MEDIA_ROOT / str(self.object.name)) + '.csv'
        table = etl.fromcsv(csv)
        group = self.request.GET.getlist('group', None)
        if group:
            context['buttons'] = {field: [url('group',xor(group, [field])), field in group] for field in etl.header(table)}
            context['header'] = {field: '' for field in group + ['Count']}
            context['load'] = url('group', None)
            context['rows'] = table.aggregate(key=group[0] if len(group)==1 else group, aggregation=len).records()
        else:
            load = int(self.request.GET.get('load', 10))
            context['header'] = {field: url('group',field) for field in etl.header(table)}
            table = table.head(load + 1)
            if table.len() > load + 1:  # Notice: table header is counted as a row too
                context['load_more'] = url('load', load + 10)
            context['rows'] = table.head(load).records()
        return context


class CollectionListView(ListView):
    model = Collection
    template_name = 'collection_list.html'
    context_object_name = 'collection_list'
    ordering = ['-created']

    def get(self, request, *args, **kwargs):
        self.object_list = self.get_queryset()
        context = self.get_context_data()
        context['PAUSE_BEFORE_START_NEW_FETCH'] = settings.PAUSE_BEFORE_START_NEW_FETCH
        return self.render_to_response(context)

    def post(self, request):
        defer(fetch, {'args': [Collection.objects.create()]})
        return redirect('collection-list', permanent=False)
