# -*- encoding: utf-8 -*-
##############################################################################
#
# Copyright (c) 2013 Andrei Levin (andrei.levin at didotech.com)
#                          All Rights Reserved.
#
# WARNING: This program as such is intended to be used by professional
# programmers who take the whole responsability of assessing all potential
# consequences resulting from its eventual inadequacies and bugs
# End users who are looking for a ready-to-use solution with commercial
# garantees and support are strongly adviced to contract a Free Software
# Service Company
#
# This program is Free Software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA  02111-1307, USA.
#
##############################################################################

import time
from report import report_sxw
import pooler


class crm_meeting_report_by_province(report_sxw.rml_parse):

    def __init__(self, cr, uid, name, context):
        super(crm_meeting_report_by_province, self).__init__(cr, uid, name, context=context)
        self.month = False
        self.year = False
        self.localcontext.update({
            'time': time,
            'get_provinces': self.get_provinces,
        })

    def get_provinces(self, form):
        meeting_obj = pooler.get_pool(self.cr.dbname).get('crm.meeting')
        provinces = {}
        
        meeting_ids = meeting_obj.search(self.cr, self.uid, [('date', '>=', form['date_from']), ('date', '<=', form['date_to'])])
        
        if meeting_ids:
            for meeting in meeting_obj.browse(self.cr, self.uid, meeting_ids):
                if meeting.partner_address_id.province:
                    province = meeting.partner_address_id.province
                    province_id = province.id
                    province_name = province.name
                else:
                    province_id = 0
                    province_name = 'unknown'
                    
                if not province_id in provinces:
                    provinces[province_id] = {
                        'id': province_id,
                        'name': province_name,
                        'meetings': []
                    }
                if not meeting.description:
                    meeting.description = meeting.name
                provinces[province_id]['meetings'].append(meeting)
                
            return provinces.values()
        else:
            return [{
                'id': 0,
                'name': 'Unknown',
                'meetings': [],
            }]

report_sxw.report_sxw('report.crm.meeting.province', 'crm.meeting', 'crm_lead_correct/report/crm_meeting_report_by_province.rml', parser=crm_meeting_report_by_province, header='internal')
