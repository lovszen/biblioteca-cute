from django.views.generic import ListView, DetailView
from django.views.generic.edit import CreateView, DeleteView
from django.urls import reverse_lazy
from django.contrib import messages 
from django.shortcuts import redirect, get_object_or_404
from django.db.models import F 
from django.utils import timezone 
from django.db import transaction
from .models import Prestamo 
from libros.models import Libro 

class PrestamoListado(ListView):
    model = Prestamo
    context_object_name = 'prestamos'
    template_name = 'prestamos/prestamo_listado.html'
    paginate_by = 10

class PrestamoDetalle(DetailView):
    model = Prestamo
    context_object_name = 'prestamo'
    template_name = 'prestamos/prestamo_detalle.html'

class PrestamoCrear(CreateView):
    model = Prestamo
    fields = ['libro', 'usuario']
    template_name = 'prestamos/prestamo_formulario.html'
    success_url = reverse_lazy('prestamos:listado')

    def form_valid(self, form):
        libro_seleccionado = form.cleaned_data['libro']
        with transaction.atomic():
            libro = Libro.objects.select_for_update().get(pk=libro_seleccionado.pk)
            
            if libro.stock > 0:
                self.object = form.save()
                libro.stock -= 1
                libro.save()
                
                messages.success(self.request, f'✅ Préstamo registrado. Stock de "{libro.titulo}" actualizado.')
                return redirect(self.get_success_url())
            else:
                messages.error(self.request, f'❌ Error: No hay stock disponible para "{libro.titulo}".')
                return self.form_invalid(form)

class PrestamoEliminar(DeleteView):
    model = Prestamo
    template_name = 'prestamos/prestamo_confirmar_eliminacion.html'
    success_url = reverse_lazy('prestamos:listado')
    
    def form_valid(self, request, *args, **kwargs):
        prestamo = self.get_object()
        if not prestamo.devuelto:
            prestamo.libro.stock += 1
            prestamo.libro.save()
            messages.info(self.request, f'Stock de "{prestamo.libro.titulo}" restaurado.')
        return super().form_valid(request, *args, **kwargs)

def marcar_devuelto(request, pk):
    """Marca un préstamo como devuelto y aumenta el stock del libro (R5)."""
    prestamo = get_object_or_404(Prestamo, pk=pk)
    
    if not prestamo.devuelto:
        prestamo.devuelto = True
        prestamo.fecha_devolucion = timezone.now().date()
        prestamo.save()
        prestamo.libro.stock += 1
        prestamo.libro.save()
        
        messages.success(request, f'✅ Libro "{prestamo.libro.titulo}" devuelto. Stock actualizado.')
    else:
        messages.warning(request, f'ℹ️ El libro ya estaba marcado como devuelto.')
    
    return redirect('prestamos:listado')