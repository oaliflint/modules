#############################################################################
#
#    PT. PROWEB INDONESIA.
#
#    Copyright (C) 2021-TODAY PROWEB INDONESIA(<https://www.proweb.co.id>)
#    Author: Junus J Djunawidjaja
#
#    You can modify it under the terms of the GNU LESSER
#    GENERAL PUBLIC LICENSE (LGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################

from odoo import api, fields, models
from odoo.exceptions import ValidationError
import xlsxwriter
import datetime
from pytz import timezone
import pytz
from io import BytesIO

try:
    from base64 import encodebytes
except ImportError:
    from base64 import encodestring as encodebytes

class KartuStokReport(models.AbstractModel):
    _name = 'report.proweb_kartu_stok.print_kartu_stok_proweb'
    _description = 'Print Kartu Stok Report ProWeb'

    @api.model
    def _get_report_values(self, docids, data=None):
        if data:
            if data['ids'] and data['context']['active_model'] in ['product.template', 'product.product']:
                docs = self.env['product.product'].browse(data['ids'])  # the model has already product.product (not product.template) because the 'ids' has been converted become product.product
                location = self.env['stock.location'].browse(data['location_id'])
                location_name = location['display_name'].split('/')[0]
                if data['day_date'] == 'day':
                    d_delta = datetime.timedelta(days=data['previous_number_days'])
                    data['date_from'] = datetime.datetime.now() - d_delta
                    data['date_to'] = None
                elif data['day_date'] == 'date':
                    if data['date_from']:
                        data['date_from'] = datetime.datetime.strptime(data['date_from'], "%Y-%m-%d")
                    if data['date_to']:
                        data['date_to'] = datetime.datetime.strptime(data['date_to'], "%Y-%m-%d")
                    
                return {
                    'ids': docs.ids,
                    'model': 'product.product',
                    'location_id': data['location_id'],
                    'location_name': location_name,
                    'date_from': data['date_from'],
                    'date_to': data['date_to'],
                    'docs': docs,
                }

class KartuStokWizard(models.TransientModel):
    _name = 'kartu.stok.wizard'
    _description = "Kartu Stok Report PDF Wizard"
    
    _default_previous_number_days = 60
    
    @api.constrains('previous_number_days')
    def _check_previous_number_days(self):
        for rec in self:
            if rec['day_date'] == 'day' and rec['previous_number_days'] <= 0:
                raise ValidationError('Number of days must more than 0')
    
    
    @api.constrains('date_from', 'date_to')
    def _check_date(self):
        for rec in self:
            if rec['day_date'] == 'date' and rec['date_from'] and rec['date_to']:
                if rec['date_from'] > rec['date_to']:
                    raise ValidationError('Date From must be earlier or same than Date To')

    @api.model
    def _default_date_from(self):
        today = datetime.date.today()
        date_start = today - datetime.timedelta(days=self._default_previous_number_days)
        return date_start
    
    @api.model
    def _default_date_to(self):
        today = datetime.date.today()
        return today                
    
    location_id = fields.Many2one('stock.location', string="Location", default=8, required=True)
    day_date = fields.Selection([('day', 'Day'), ('date', 'Date')], string="Select: Number Previous Days or Date Range", required=True, default='day')
    previous_number_days = fields.Integer(string="Starting from the previous number of days", default=_default_previous_number_days)
    date_from = fields.Date(string="Date From", default=_default_date_from)
    date_to = fields.Date(string="Date To", default=_default_date_to)
    fileout = fields.Binary('File', readonly=True)
    fileout_filename = fields.Char('Filename', readonly=True)

    
    def action_kartu_stok_pdf_wizard(self):
        active_ids_tmp = self.env.context.get('active_ids')
        active_model = self.env.context.get('active_model')
        if active_model == 'product.template':
            active_ids = self.env['product.product'].search(
                [('product_tmpl_id', 'in', active_ids_tmp),
                ('active', '=', True)]).ids
        else:
            active_ids = active_ids_tmp  # product.product                               
        if self.read()[0]['location_id']:
            data = { 
                'location_id': self.read()[0]['location_id'][0],
                'day_date': self.read()[0]['day_date'],
                'previous_number_days': self.read()[0]['previous_number_days'],
                'date_from': self.read()[0]['date_from'],
                'date_to': self.read()[0]['date_to'],
                'ids': active_ids,
            }
        return self.env.ref('proweb_kartu_stok.action_print_kartu_stok_proweb').report_action(active_ids, data=data)

    def action_kartu_stok_excel_wizard(self):
        active_ids_tmp = self.env.context.get('active_ids')
        active_model = self.env.context.get('active_model')
        if active_model == 'product.template':
            active_ids = self.env['product.product'].search(
                [('product_tmpl_id', 'in', active_ids_tmp),
                ('active', '=', True)]).ids
        else:
            active_ids = active_ids_tmp  # product.product                               
        if self.read()[0]['location_id']:
            data = { 
                'location_id': self.read()[0]['location_id'][0],
                'day_date': self.read()[0]['day_date'],
                'previous_number_days': self.read()[0]['previous_number_days'],
                'date_from': self.read()[0]['date_from'],
                'date_to': self.read()[0]['date_to'],
                'ids': active_ids,
                'context': {'active_model': active_model}
            }
            
            ### Workbook ###
            file_io = BytesIO()
            workbook = xlsxwriter.Workbook(file_io)

            self.generate_xlsx_report(workbook, data=data)
            
            workbook.close()
            fout=encodebytes(file_io.getvalue())
            
            datetime_string = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            report_name = 'Kartu_Stok'
            filename = '%s_%s'%(report_name,datetime_string)
            self.write({'fileout':fout, 'fileout_filename':filename})
            file_io.close()
            filename += '%2Exlsx'

            return {
                'type': 'ir.actions.act_url',
                'target': 'new',
                'url': 'web/content/?model='+self._name+'&id='+str(self.id)+'&field=fileout&download=true&filename='+filename,
            }

    def generate_xlsx_report(self, workbook, data=None, objs=None):

        bold = workbook.add_format({'bold': True})
        border_date_right = workbook.add_format({'border':1, 'num_format': 'DD-MM', 'bg_color': '#dddddd', 'align': 'right'})
        border_date_ed_center = workbook.add_format({'border':1, 'num_format': 'DD-MM-YYYY', 'bg_color': '#dddddd', 'align': 'center'})
        border_int_right = workbook.add_format({'border':1, 'num_format': '#,##0', 'bg_color': '#dddddd', 'align': 'right'})
        border_int_right_bold = workbook.add_format({'border':1, 'num_format': '#,##0', 'bg_color': '#dddddd', 'align': 'right', 'bold': True})
        border_text_left = workbook.add_format({'border':1, 'bg_color': '#dddddd', 'align': 'left'})
        border_text_center = workbook.add_format({'border':1, 'bg_color': '#dddddd', 'align': 'center'})
        border_text_center_bold = workbook.add_format({'border':1, 'bg_color': '#dddddd', 'align': 'center', 'bold': True})
        header_format_left = workbook.add_format({'bold': True, 'border':1, 'bg_color': '#808080', 'align': 'left'})
        header_format_right = workbook.add_format({'bold': True, 'border':1, 'bg_color': '#808080', 'align': 'right'})
        header_format_center = workbook.add_format({'bold': True, 'border':1, 'bg_color': '#808080', 'align': 'center'})

        def print_initial_stock(row, stock_total, has_lot, has_ed):
            sheet.write(row, 0, '', border_date_right) #date-right
            sheet.write(row, 1, '', border_date_right) #date-right
            sheet.write(row, 2, '', border_date_right) #date-right
            sheet.write(row, 3, '', border_int_right) #text-right
            sheet.write(row, 4, '', border_int_right) #text-right
            sheet.write(row, 5, '', border_int_right) #text-right
            sheet.write(row, 6, '', border_int_right) #text-right
            sheet.write(row, 7, '', border_int_right) #text-right
            sheet.write(row, 8, '', border_int_right) #text-right
            sheet.write(row, 9, stock_total, border_int_right_bold) #text-right
            col = 10
            if has_lot:
                sheet.write(row, col, '', border_text_left) #text-left
                col += 1
            if has_ed:
                sheet.write(row, col, '', border_text_center) #text-center
                col += 1
            sheet.write(row, col, '', border_text_center_bold)  # text-center
            col += 1
            # sheet.write(row, col, 'Initial Stock', border_text_center_bold) #text-center
            # col += 1
            sheet.write(row, col, '', border_text_center) #text-center
            col += 1
            sheet.write(row, col, '', border_text_center)  # text-center
            col += 1
            sheet.write(row, col, '', border_text_center)  # text-center
            col += 1

            sheet.write(row, col, '', border_text_center)  # text-center

        if data:
            if data['ids'] and data['context']['active_model'] in ['product.template', 'product.product']:
                docs = self.env['product.product'].browse(data['ids'])  # the model has already product.product (not product.template) because the 'ids' has been converted become product.product
                location = self.env['stock.location'].browse(data['location_id'])
                location_name = location['display_name'].split('/')[0]
                if data['day_date'] == 'day':
                    d_delta = datetime.timedelta(days=data['previous_number_days'])
                    data['date_from'] = datetime.datetime.now() - d_delta
                    data['date_to'] = None
                elif data['day_date'] == 'date':
                    if data['date_from']:
                        data['date_from'] = datetime.datetime.strptime(str(data['date_from']), "%Y-%m-%d")
                    if data['date_to']:
                        data['date_to'] = datetime.datetime.strptime(str(data['date_to']), "%Y-%m-%d")

                for doc in docs:
                    sheet = workbook.add_worksheet(doc.display_name)

                    row =0
                    sheet.write(row, 2, doc.display_name, bold)

                    row =1
                    sheet.write(row, 3, location_name, bold)

                    has_date_from=isinstance(data['date_from'], datetime.datetime)
                    has_date_to=isinstance(data['date_to'], datetime.datetime)
                    row =2
                    col = 1
                    if has_date_from:
                        sheet.write(row, col, "Data From:", bold)
                        col = 2
                        sheet.write(row, col, data['date_from'].strftime('%Y-%m-%d'), bold)
                        
                    if has_date_to:
                        date_to_tmp = data['date_to'] + datetime.timedelta(days=1)                    
                        col = 3
                        sheet.write(row, col, "Data To:", bold)
                        col = 4
                        sheet.write(row, col, data['date_to'].strftime('%Y-%m-%d'), bold)

                    has_lot=0
                    has_ed=0
                    for stock_move in doc.stock_move_ids:
                        for stockcards in stock_move.move_line_ids:
                            if has_ed == 0:
                                if has_date_from:
                                    if has_date_to:
                                        tmp_lines=stockcards.filtered(lambda a: (data['date_from'] <= a.date and a.date < date_to_tmp))
                                    else:
                                        tmp_lines=stockcards.filtered(lambda a: (data['date_from'] <= a.date))
                                else:
                                    tmp_lines=stockcards
                                tmp_has_lot=len(tmp_lines.filtered(lambda a: a.lot_id))
                                if tmp_has_lot:
                                    has_lot=1
                                    tmp_has_ed=len(tmp_lines.filtered(lambda a: a.lot_id and a.expiration_date))
                                    if tmp_has_ed:
                                        has_ed=1

                    row =3
                    col = 0
                    sheet.write(row, col, '#', header_format_right)  # text-right
                    sheet.set_column('A:A', 2)  # Date
                    col += 1
                    sheet.write(row, col, 'Reference', header_format_right)  # text-right
                    sheet.set_column('B:B', 20)  # Date
                    col += 1
                    sheet.write(row, col, 'Date', header_format_right) #text-right
                    sheet.set_column('C:C', 10) #Date
                    col += 1
                    sheet.write(row, col, 'Invoice Date', header_format_right) #text-right
                    sheet.set_column('D:D', 15) #Date
                    col += 1
                    sheet.write(row, col, 'Product', header_format_right)  # text-right
                    sheet.set_column('E:E', 20)  # Date
                    col += 1
                    sheet.write(row, col, 'From', header_format_right)  # text-right
                    sheet.set_column('F:F', 10)  # Date
                    col += 1
                    sheet.write(row, col, 'To', header_format_right)  # text-right
                    sheet.set_column('G:G', 10)  # Date
                    col += 1
                    sheet.write(row, col, 'In', header_format_right) #text-right
                    col += 1
                    sheet.write(row, col, 'Out', header_format_right) #text-right
                    sheet.set_column('H:I', 8)  #In, Out
                    col += 1
                    sheet.write(row, col, 'Stock', header_format_right) #text-right
                    sheet.set_column('K:K', 10) #Stock
                    if has_lot:
                        col += 1
                        sheet.write(row, col, 'Lot/SN', header_format_left) #text-left                            
                        sheet.set_column('J:J', 25) #Lot/SN
                        if has_ed:
                            col += 1
                            sheet.write(row, col, 'ED', header_format_center) #text-center
                            sheet.set_column('L:L', 10) #ED
                            sheet.set_column('M:N', 25) #Distributor, Buyer
                        else:
                            sheet.set_column('J:K', 25) #Distributor, Buyer
                    else:
                        sheet.set_column('K:L', 25) #Distributor, Buyer
                    col += 1

                    sheet.write(row, col, 'Origin', header_format_center)  # text-cent
                    col += 1
                    # sheet.write(row, col, 'Distributor', header_format_center) #text-center
                    # col += 1
                    sheet.write(row, col, 'Contact', header_format_center) #text-center
                    col += 1
                    sheet.write(row, col, 'Price Unit', header_format_center) #text-center
                    col += 1
                    sheet.write(row, col, 'Price UOM', header_format_center) #text-center
                    col += 1

                    sheet.write(row, col, 'State', header_format_center) #text-center

                    stock_show_initial=0
                    stock_total=0
                    row += 1
                    col = 0
                    count=1
                    # excluded_ids = []
                    # for move in doc.stock_move_ids.sorted(key=lambda sm: sm.id):
                    #     if move.returned_move_ids:
                    #         for returned_move in returned_move_ids:
                    #             excluded_ids.append(returned_move.id)
                    #             if returned_move.

                    # inv = self.env['account.move'].search([('state', '!=', 'done')])
                    exculded_moves = []
                    for stock_move in doc.stock_move_ids.sorted(key=lambda sm: sm.id):
                        if stock_move.origin_returned_move_id:
                            exculded_moves.append(stock_move.origin_returned_move_id.id)
                            exculded_moves.append(stock_move.id)
                        # if stock_move.picking_id.origin in inv.mapped('name'):
                        #     tt.append(stock_move)

                    for stock_move in doc.stock_move_ids.filtered(lambda x:x.id not in exculded_moves).sorted(key=lambda sm: sm.id):
                        # returned_move_ids = stock_move.returned_move_ids.ids
                        # for move in stock_move.returned_move_ids.mapped('move_orig_ids'):
                        #     returned_move_ids.append(move.id)
                        for stockcards in stock_move.move_line_ids:
                            for stock_move in stockcards:
                                # inv = False
                                # if stock_move.origin:
                                #     inv = self.env['account.move'].search([('name', '=', stock_move.origin)], limit=1)
                                # if stock_move.picking_id.picking_type_id.name== "Returns":
                                # if stock_move.picking_id.origin:
                                #     returned_picking = False
                                #     if 'Return of' in stock_move.picking_id.origin:
                                #         returned_picking = stock_move.picking_id.origin.split('Return of')[0]
                                #     elif 'إرجاع' in stock_move.picking_id.origin:
                                #         returned_picking = stock_move.picking_id.origin.split('إرجاع')[0]
                                #     print(returned_picking,'fffffffffffffff')
                                # else:
                                if stock_move.state == 'done':
                                            if stock_move.location_id.id == data['location_id'] or stock_move.location_dest_id.id == data['location_id']:
                                                smdate=stock_move.date
                                                if not has_date_to or (smdate.strftime('%Y-%m-%d') < date_to_tmp.strftime('%Y-%m-%d')):
                                                    if not has_date_from or (smdate.strftime('%Y-%m-%d') >= data['date_from'].strftime('%Y-%m-%d')):
                                                        if stock_show_initial == 0:
                                                            stock_show_initial=1
                                                            print_initial_stock(row, stock_total, has_lot, has_ed)
                                                        row += 1
                                                        col = 0
                                                        sheet.write(row, col, count, border_int_right)  # date-right
                                                        count+=1
                                                        col += 1
                                                        sheet.write(row, col, stock_move.reference, border_date_right)  # date-right
                                                        col += 1

                                                        sheet.write(row, col, stock_move.date, border_date_right) #date-right
                                                        col += 1
                                                        inv_date = ''
                                                        if stock_move.origin:
                                                            inv = self.env['account.move'].search(
                                                                [('name', '=', stock_move.origin)], limit=1)
                                                            inv_date = inv.invoice_date

                                                        sheet.write(row, col, inv_date, border_date_right)  # date-right
                                                        col += 1
                                                        sheet.write(row, col, stock_move.product_id.name, border_date_right)  # date-right
                                                        col += 1
                                                        sheet.write(row, col, stock_move.location_id.name_get()[0][1],
                                                                    border_date_right)  # date-right
                                                        col += 1
                                                        sheet.write(row, col, stock_move.location_dest_id.name_get()[0][1],
                                                                    border_date_right)  # date-right
                                                        col += 1
                                                        converted_qty = stock_move.product_uom_id._compute_quantity(
                                                            stock_move.qty_done, stock_move.product_id.unique_uom_id)

                                                        if stock_move.location_dest_id.id == data['location_id']:
                                                            sheet.write(row, col, converted_qty, border_int_right) #int-right
                                                            stock_total=stock_total + converted_qty
                                                        else:
                                                            sheet.write(row, col, '', border_int_right) #int-right
                                                        col += 1

                                                        if stock_move.location_id.id == data['location_id']:

                                                            sheet.write(row, col, converted_qty, border_int_right) #int-right
                                                            stock_total=stock_total - converted_qty
                                                        else:
                                                            sheet.write(row, col, '', border_int_right) #int-right
                                                        col += 1

                                                        sheet.write(row, col, stock_total, border_int_right) #int-right
                                                        col += 1

                                                        if has_lot:
                                                            if stock_move.lot_id:
                                                                sheet.write(row, col, stock_move.lot_id.name, border_text_left) #text-left
                                                            else:
                                                                sheet.write(row, col, '', border_text_left) #text-left
                                                            col += 1
                                                            if has_ed:
                                                                if stock_move.lot_id:
                                                                    sheet.write(row, col, stock_move.lot_id.expiration_date, border_date_ed_center) #date-ed-center
                                                                else:
                                                                    sheet.write(row, col, '', border_date_ed_center) #date-ed-center
                                                                col += 1
                                                        sheet.write(row, col, stock_move.origin, border_int_right)  # int-right
                                                        col += 1

                                                        if stock_move.location_dest_id.id == data['location_id']:
                                                            if stock_move.picking_id and stock_move.picking_id.origin:
                                                                sheet.write(row, col, stock_move.picking_id.partner_id.name, border_text_center) #text-center
                                                            else:
                                                                if stock_move.location_id:
                                                                    if stock_move.location_id.name == 'Inventory adjustment':
                                                                        sheet.write(row, col, 'Adjust *', border_text_center) #text-center
                                                                    else:
                                                                        sheet.write(row, col, stock_move.location_id.location_id.name  + ' *', border_text_center) #text-center
                                                                else:
                                                                    sheet.write(row, col, doc.seller_ids[0].name + ' *', border_text_center) #text-center
                                                        # else:
                                                        #     sheet.write(row, col, '', border_text_center) #text-center
                                                        # col += 1

                                                        elif stock_move.location_id.id == data['location_id']:
                                                            if stock_move.picking_id and stock_move.picking_id.origin:
                                                                sheet.write(row, col, stock_move.picking_id.partner_id.name, border_text_center) #text-center
                                                            else:
                                                                if stock_move.location_dest_id:
                                                                    if stock_move.location_dest_id.name == 'Inventory adjustment':
                                                                        sheet.write(row, col, 'Adjust *', border_text_center) #text-center
                                                                    else:
                                                                        sheet.write(row, col, stock_move.location_dest_id.location_id.name + ' *', border_text_center) #text-center
                                                                else:
                                                                    sheet.write(row, col, doc.seller_ids[0].name + ' *', border_text_center) #text-center
                                                        else:
                                                            sheet.write(row, col, '', border_text_center) #text-center
                                                        col += 1
                                                        sheet.write(row, col, stock_move.price_unit, border_text_center)
                                                        col += 1
                                                        sheet.write(row, col, stock_move.product_uom_id.name, border_text_center)
                                                        col += 1

                                                        sheet.write(row, col, stock_move.state, border_text_center)
                                                        col = 0
                                                    else:
                                                        converted_qty = stock_move.product_uom_id._compute_quantity(
                                                            stock_move.qty_done, stock_move.product_id.unique_uom_id)
                                                        if stock_move.location_dest_id.id == data['location_id']:
                                                            stock_total=stock_total + converted_qty
                                                        if stock_move.location_id.id == data['location_id']:
                                                            stock_total=stock_total - converted_qty
                    if stock_show_initial == 0:
                        print_initial_stock(row, stock_total, has_lot, has_ed)
